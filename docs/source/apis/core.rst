Core
====

tomobase.core

.. list-table::
   :header-rows: 1

   * - globals
     - Type
     - Description
   * - proxy
     - :py:class:`~tomobase.core.environment.EnvironmentContext`
     - global class instance to switch between devices e.g. CPU and GPU
   * - logger
     - :py:class:`~tomobase.core.log.LogHandler`
     - global logger instance for logging messages
   * - progress
     - :py:class:`~tomobase.core.prog.ProgressHandler`
     - global progress handler instance for tracking progress


.. list-table::
   :header-rows: 1

   * - Register
     - Type
     - Decorator
     - Description
   * - image
     - :py:class:`~tomobase.core.base_classes.registers.Registry`
     - None
     - Registry of image types(:py:class:`~tomobase.core.base_classes.ImageAbstract`)
   * - tiltschemes
     - :py:class:`~tomobase.core.base_classes.registers.Registry`
     - None
     - Registry of tiltscheme types(:py:class:`~tomobase.core.base_classes.tiltscheme.TiltSchemeAbstract`)
   * - procedures
     - :py:class:`~tomobase.core.base_classes.registers.Registry`
     - :py:func:`~tomobase.core.bootstraps.base.bootstap_procedure`
     - Registry of procedure types(:py:class:`Callable`)
       
       This is categorized using the categories registry.
   * - categories
     - :py:class:`~tomobase.core.base_classes.registers.HierarchicalRegistry`
     - None
     - Hierarchical registry for categorizing reconstruction procedures


Environment
---------
tomobase.core.environment

.. autoclass:: tomobase.core.environment.GPUContext
   :members:
   :member-order: bysource
   :show-inheritance:

.. autoclass:: tomobase.core.environment.EnvironmentContext
   :members:
   :member-order: bysource
   :show-inheritance:


Logging
---------
tomobase.core

.. autoclass:: tomobase.core.log.LogHandler
   :members:
   :member-order: bysource
   :show-inheritance:

.. autoclass:: tomobase.core.prog.ProgressHandler
   :members:
   :member-order: bysource
   :show-inheritance:

Utilities
---------

tomobase.core.utils

.. autofunction:: tomobase.core.utils.iter_indexers_with_len
.. autofunction:: tomobase.core.utils.geometries._get_weights
.. autofunction:: tomobase.core.utils.geometries.format_before_projection
.. autofunction:: tomobase.core.utils.geometries.format_after_projection
.. autoclass:: tomobase.core.utils.geometries.Projector
   :members:
   :member-order: bysource
   :show-inheritance:    


Base Classes
---------

tomobase.core.base_classes

.. autoclass:: tomobase.core.base_classes.registers.Registry
   :members:
   :member-order: bysource
   :show-inheritance:

.. autoclass:: tomobase.core.base_classes.registers.HierarchicalRegistry
   :members:
   :member-order: bysource
   :show-inheritance:

.. autoclass:: tomobase.core.base_classes.image.ImageAbstract
   :members:
   :member-order: bysource
   :show-inheritance:

.. autoclass:: tomobase.core.base_classes.measurement.MeasurementAbstract
   :members:
   :member-order: bysource
   :show-inheritance:

.. autoclass:: tomobase.core.base_classes.tiltscheme.TiltSchemeAbstract
   :members:
   :member-order: bysource
   :show-inheritance:

.. autoclass:: tomobase.core.base_classes.tiltscheme.TiltSchemeCursor
   :members:
   :member-order: bysource
   :show-inheritance:


Components
**********



.. autoclass:: tomobase.core.base_classes.components.context_model.ContextModel
   :members:
   :member-order: bysource
   :show-inheritance:

.. autoclass:: tomobase.core.base_classes.components.signal_model.SignalModel
   :members:
   :member-order: bysource
   :show-inheritance:

.. autoclass:: tomobase.core.base_classes.components.io_model.IOModel
   :members:
   :member-order: bysource
   :show-inheritance:

.. autoclass:: tomobase.core.base_classes.components.register.RegistryBase
   :members:
   :member-order: bysource
   :show-inheritance:


Bootstrap Functions
---------
tomobase.core.bootstraps

.. autofunction:: tomobase.core.bootstraps.base.bootstap_procedure

Packages
--------
tomobase.core.packages

.. autofunction:: tomobase.core.packages.add_package


.. tip::
    This is a key for remembering what the syntaxing looks like in rst files

.. note::

   Important note.

.. admonition:: Experimental