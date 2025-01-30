# Clixon Python API Changelog

## 1.3.0
30 January 2025

### Features:
* Added device_open() method.
* Make the argument parser handle extra arguments which can be added after --
* New rpc_apply_rpc_template method for RPC templates.

### Corrected bugs:
* Optimize hooks, make sure we don't execute the Clixon() context twice.
* RPC apply: Only return the device data in response.
* Remove appending class proprties to property cache.  Correct element … by @NetworkOverload in https://github.com/clicon/clixon-pyapi/pull/30
* Element class bugfixes by @NetworkOverload in https://github.com/clicon/clixon-pyapi/pull/33

### New Contributors
* @NetworkOverload made their first contribution in https://github.com/clicon/clixon-pyapi/pull/30

## 1.1.0
03 June 2024

### New features

* Feature: Added get_data which wraps get_value.
* Added Element.find()
* Added Element.findall() which is a wrapper around get_elements().
* Element.get_elements() can now retreive all child elements.
* Element.parent() return the parent element.
* Elements.parents() now return an iterator with all parent elements.
* Extended delete, now possible to remove youself with element.delete()
* Extended delete to take an element as argument.

### Corrected bugs

* [API: Add "show devices diff"](https://github.com/clicon/clixon-pyapi/issues/22)
* [Add method to do "show compare"](https://github.com/clicon/clixon-pyapi/issues/19)
* [Make sure certain functions times out instead of hangs forever](https://github.com/clicon/clixon-pyapi/issues/18)
* [Add method for apply_service](https://github.com/clicon/clixon-pyapi/issues/17)
* [get_path should now handle arguments with backslash in them](https://github.com/clicon/clixon-pyapi/issues/24)
* Module filters should use the module name, not the whole module path.
* When creating new XML nodes the parent object was not set to the actual parent.
* NO_CLIXON_ARGS can now be set to disable the arguement parser.
* Don't re-enable notifications in Clixon.apply_service()
* Make sure we don't enable transaction notifications twice.
* [API: get_path should handle ' as well as " in path](https://github.com/clicon/clixon-pyapi/issues/23)
* Clixon.set_root() did not use edit-config.

## 1.0
12 March 2024

Clixon Python API 1.0 is a first major release of the Clixon
controller Python API. It supports the 1.0 Clixon controller release.
