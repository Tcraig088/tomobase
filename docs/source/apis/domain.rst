Domain
======
.. py:data:: tomobase.domain


Procedures
----------
.. py:data:: tomobase.domain.procedures

The raw functions can be found in :py:mod:`tomobase.domain.procedures`. Howeverm it is recomennded to use these functions through the register :py:mod:`tomobase.procedures` after initialization which provides more flexibility and extends their applicability.

Phantoms
********
.. py:data:: tomobase.domain.procedures.phantoms

Functions to generate or fetch saved phantoms as :py:mod:`Volume`

.. autofunction:: tomobase.domain.phantoms.get_nanocage
.. autofunction:: tomobase.domain.phantoms.get_nanocube
.. autofunction:: tomobase.domain.phantoms.get_nanorod

Deformations
************
.. py:data:: tomobase.domain.procedures.deformations

Functions to deform a Volume for simulating test cases for algorithm developement.

.. autofunction:: tomobase.domain.procedures.deformations.beamdamage
.. autofunction:: tomobase.domain.procedures.deformations.melting

Projections
***********
.. py:data:: tomobase.domain.procedures.projections

.. autofunction:: tomobase.domain.procedures.reconstruct.forward_project.project

Reconstructions
***************
.. py:data:: tomobase.domain.procedures.reconstructions

Functions to perform various reconstruction algorithms.

.. autofunction:: tomobase.domain.procedures.reconstruct.back_project.reconstruct_tvm
.. autofunction:: tomobase.domain.procedures.reconstruct.back_project.reconstruct_sirt
.. autofunction:: tomobase.domain.procedures.reconstruct.back_project.reconstruct_wbp
.. autofunction:: tomobase.domain.procedures.reconstruct.back_project.reconstruct_mlem

Image Processing
****************
.. py:data:: tomobase.domain.procedures.image_processing
Functions to perform various image processing algorithms.

Background Corrections
~~~~~~~~~~~~~~~~~~~~~~~

Misalignments
~~~~~~~~~~~~~~

Scaling
~~~~~~~

io
----------
.. py:data:: tomobase.domain.io

Functions to perform various io operations. 
These functions can be used directly with the registry :py:mod:`tomobase.domain.io` or they can be used through the registers in :py:mod:`~tomobase.base_classes.components.io_model.IOModel`.write() or :py:mod:`~tomobase.base_classes.components.io_model.IOModel`.read() methods.
See the IOModel documentation for more details.

.. autofunction:: tomobase.domain.io.emi.read_emi
.. autofunction:: tomobase.domain.io.h5.read_h5
.. autofunction:: tomobase.domain.io.h5.write_h5


Data_Classes
----------
.. py:data:: tomobase.core.data_classes

classes showing the ability of each 

.. autoclass:: tomobase.core.data_classes.images.Sinogram
   :members:
   :member-order: bysource
   :show-inheritance:

.. autoclass:: tomobase.core.data_classes.images.Volume
   :members:
   :member-order: bysource
   :show-inheritance:

.. autoclass:: tomobase.core.data_classes.images.Image
   :members:
   :member-order: bysource
   :show-inheritance:

.. autoclass:: tomobase.core.data_classes.Measurement
   :members:
   :member-order: bysource
   :show-inheritance:

.. autoclass:: tomobase.core.data_classes.tiltschemes.GRS
   :members:
   :member-order: bysource
   :show-inheritance:

.. autoclass:: tomobase.core.data_classes.tiltschemes.Incremental
   :members:
   :member-order: bysource
   :show-inheritance:

