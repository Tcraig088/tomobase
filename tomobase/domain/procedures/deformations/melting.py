from ....core.data_classes.images import Volume
from ....core import registers, utils, get_xp


def _get_attachable_mask(melted_mask, object_mask, xp, ndimage, kernel):
    neighbor_count = ndimage.convolve(
        object_mask.astype(xp.int32),
        kernel,
        mode="constant",
        cval=0,
    )

    return (~melted_mask) & (neighbor_count > 0)

@registers.procedures.register(name='Melting', category=registers.categories['Deform'])
def melting(
    volume: Volume,
    migration_probability: float = 0.1,
    max_centroids: int | None = None,
    disable_addition: bool = False,
):
    xp = get_xp(volume.data)
    ndimage = utils.get_module('ndimage', volume.context)

    data = volume.data
    mask = data != 0

    neighbor_kernel = xp.ones((3, 3, 3), dtype=xp.int32)
    neighbor_kernel[1, 1, 1] = 0

    erosion_structure = xp.ones((3, 3, 3), dtype=bool)

    # Original labels are used only to preserve object identity.
    labels, num_objects = ndimage.label(mask)

    if num_objects == 0:
        return volume

    # ------------------------------------------------------------
    # 1. Surface-only probabilistic removal
    # ------------------------------------------------------------

    neighbor_count = ndimage.convolve(
        mask.astype(xp.int32),
        neighbor_kernel,
        mode="constant",
        cval=0,
    )

    interior_mask = ndimage.binary_erosion(
        mask,
        structure=erosion_structure,
        border_value=0,
    )

    surface_mask = mask & ~interior_mask

    connectivity_strength = neighbor_count / 26.0

    removal_probability = migration_probability * (1.0 - connectivity_strength)
    removal_probability = xp.where(surface_mask, removal_probability, 0.0)

    remove_mask = xp.random.random(mask.shape) < removal_probability

    melted_data = data.copy()
    melted_data[remove_mask] = 0

    # ------------------------------------------------------------
    # 2. Keep only the largest N remaining clusters
    # ------------------------------------------------------------

    if max_centroids is not None and max_centroids > 0:
        melted_mask = melted_data != 0

        cluster_labels, num_clusters = ndimage.label(melted_mask)

        if num_clusters > max_centroids:
            cluster_sizes = xp.bincount(cluster_labels.ravel())

            # Ignore background label 0.
            cluster_sizes[0] = 0

            keep_cluster_ids = xp.argsort(cluster_sizes)[-max_centroids:]

            keep_mask = xp.isin(cluster_labels, keep_cluster_ids)
            discard_mask = melted_mask & ~keep_mask

            melted_data[discard_mask] = 0

            # Treat discarded clusters as voxels to be migrated/re-added.
            remove_mask = remove_mask | discard_mask

    if disable_addition:
        volume.xr.data = melted_data
        return volume

    # ------------------------------------------------------------
    # 3. Re-add removed voxels by inverse-probability filling:
    #    fill the most-connected vacant boundary voxels first.
    # ------------------------------------------------------------

    removed_values = data[remove_mask]

    if removed_values.shape[0] == 0:
        volume.xr.data = melted_data
        return volume

    melted_mask = melted_data != 0

    # Use original labels only to grow from existing surviving objects.
    for label_id in range(1, int(num_objects) + 1):
        object_mask = (labels == label_id) & melted_mask

        if not xp.any(object_mask):
            continue

        # Number of removed voxels originally belonging to this object.
        object_removed_mask = (labels == label_id) & remove_mask
        object_removed_values = data[object_removed_mask]

        if object_removed_values.shape[0] == 0:
            continue

        for i in range(object_removed_values.shape[0]):
            attachable_mask = _get_attachable_mask(
                melted_mask=melted_mask,
                object_mask=object_mask,
                xp=xp,
                ndimage=ndimage,
                kernel=neighbor_kernel,
            )

            candidates = xp.argwhere(attachable_mask)

            if candidates.shape[0] == 0:
                break

            # Count how connected each candidate is to the full current volume.
            candidate_connectivity = ndimage.convolve(
                melted_mask.astype(xp.int32),
                neighbor_kernel,
                mode="constant",
                cval=0,
            )

            candidate_scores = candidate_connectivity[tuple(candidates.T)]

            attach_pos = candidates[xp.argmax(candidate_scores)]

            melted_data[tuple(attach_pos)] = object_removed_values[i]

            melted_mask[tuple(attach_pos)] = True
            object_mask[tuple(attach_pos)] = True

    volume.xr.data = melted_data
    return volume