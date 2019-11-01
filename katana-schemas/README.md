# Katana Slice Information Model

## Structure of the IM
Katana Slice IM has three sections:

* Generic Network Slice Template (GNST)
* Vertical Services Descriptor
* Test Descriptor

## Sources
The GNST is based on the [GSMA GNST v1.0](https://www.gsma.com/newsroom/wp-content/uploads//NG.116-v1.0.pdf)
and [GSMA GNST v2.0](https://www.gsma.com/newsroom/wp-content/uploads//NG.116-v2.0.pdf)

Katana Slice Information Model follows the JSON Schema model, on which OpenAPIs are based:

* [Source](http://json-schema.org/)
* [Understanding JSON Schema](http://json-schema.org/understanding-json-schema/UnderstandingJSONSchema.pdf)

## Useful Tools
* [JSON Validator](https://jsonlint.com/)
* [YAML Validator](http://www.yamllint.com/)
* [JSON Schema Validator](https://www.jsonschemavalidator.net/)
* [JSON Schema Generator](https://jsonschema.net/)

## GNST values
### GNST Included
* sliceid
* delay_tolerance
* deterministic_communication
    - availability
    - periodicity
* network_DL_throughput
    - guaranteed
    - maximum
* ue_DL_throughput
    - guaranteed
    - maximum
* group_communication_support
* isolation_level
    - physical isolation
    - logical isolation
* mtu
* mission_critical_support
    - availability
    - mc_service
* mmtel_support
* Network Slice Customer network functions --> It is covered by the service_descriptor section
* nb_iot
* Perofrmance Monitoring --> It is covered by the test_descriptor section
* Performance Prediction --> It is covered by the test_descriptor section
* positional_support
    - availability
    - frequency
    - accuracy
* radio_spectrum
* simultaneous_nsi

### Not included
* Energy efficiency
* Location based message delivery
* Reliability --> Not defined yet
* Availability --> Not defined yet
* Root cause investigation
* Session and Service Continuity support