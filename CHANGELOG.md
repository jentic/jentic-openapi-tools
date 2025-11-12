# CHANGELOG

<!-- version list -->

## v1.0.0-alpha.17 (2025-11-12)

### Chores

- **validator-spectral**: Delete testing OpenAPI Document
  ([`d131766`](https://github.com/jentic/jentic-openapi-tools/commit/d13176643a188729167b9bc91556ca85f6956fd9))

### Documentation

- **validator-spectral**: Add note about JavaScript Ruleset format
  ([`df358e2`](https://github.com/jentic/jentic-openapi-tools/commit/df358e2b554d466bbe8d317ea607a67963f0f959))

### Features

- Update @redocly/cli to v2.11.1 ([#124](https://github.com/jentic/jentic-openapi-tools/pull/124),
  [`36e6724`](https://github.com/jentic/jentic-openapi-tools/commit/36e6724737cf88ece5780f898b23672d54923aa7))


## v1.0.0-alpha.16 (2025-11-10)

### Bug Fixes

- **validator**: Fix DataFieldValue type hint
  ([#116](https://github.com/jentic/jentic-openapi-tools/pull/116),
  [`138baa3`](https://github.com/jentic/jentic-openapi-tools/commit/138baa394e16dd6f49dd35f638cb566ae390e0b0))

- **validator-spectral**: Avoid validating XML examples
  ([#123](https://github.com/jentic/jentic-openapi-tools/pull/123),
  [`a66b638`](https://github.com/jentic/jentic-openapi-tools/commit/a66b638b1e0bf5cb38e57a604bd0374d3a98b32e))

### Features

- **datamodels**: Add low model for Contact spec object
  ([#117](https://github.com/jentic/jentic-openapi-tools/pull/117),
  [`937e613`](https://github.com/jentic/jentic-openapi-tools/commit/937e613c1d9ba0c9a196c541c94dc80b83cdcf8e))

- **datamodels**: Add low model for Info spec object
  ([#119](https://github.com/jentic/jentic-openapi-tools/pull/119),
  [`a3bcde6`](https://github.com/jentic/jentic-openapi-tools/commit/a3bcde6eac2873e2564f569fc05b36de96cb8f09))

- **datamodels**: Add low model for License spec object
  ([#118](https://github.com/jentic/jentic-openapi-tools/pull/118),
  [`aaa8f77`](https://github.com/jentic/jentic-openapi-tools/commit/aaa8f779fb02c72d810316beeaf92be13ac1b2f2))

- **datamodels**: Add low model for Server Variable spec object
  ([#121](https://github.com/jentic/jentic-openapi-tools/pull/121),
  [`49b707f`](https://github.com/jentic/jentic-openapi-tools/commit/49b707f03ee37261d7ad1f81371c438ecd8d3bec))

- **datamodels**: Add ValueSource wrapping to Schema required and enum fields
  ([#122](https://github.com/jentic/jentic-openapi-tools/pull/122),
  [`a53ee68`](https://github.com/jentic/jentic-openapi-tools/commit/a53ee68f48647218a5ec0e47bce91d3e0224675c))


## v1.0.0-alpha.15 (2025-11-04)

### Bug Fixes

- Exclude base backends from project entrypoints
  ([#115](https://github.com/jentic/jentic-openapi-tools/pull/115),
  [`ed72ca1`](https://github.com/jentic/jentic-openapi-tools/commit/ed72ca175b85c283c0f684fbb23bb5bb3b64d7f1))


## v1.0.0-alpha.14 (2025-11-03)

### Features

- **validator**: Add `JsonValue` type for enhanced data handling
  ([`d585e8e`](https://github.com/jentic/jentic-openapi-tools/commit/d585e8eb9b6a677652f0203559d859432f2b68fd))


## v1.0.0-alpha.13 (2025-11-03)

### Features

- **datamodels**: Add low model for External Documentation spec object
  ([#107](https://github.com/jentic/jentic-openapi-tools/pull/107),
  [`fc4c12a`](https://github.com/jentic/jentic-openapi-tools/commit/fc4c12aca989eeed445c8613409e12544103c11e))

- **datamodels**: Add low model for Schema spec object
  ([#110](https://github.com/jentic/jentic-openapi-tools/pull/110),
  [`09fcdf4`](https://github.com/jentic/jentic-openapi-tools/commit/09fcdf41e47b7bb1cde84bb8ae1694c9abead834))

- **datamodels**: Add low model for Tag spec object
  ([#109](https://github.com/jentic/jentic-openapi-tools/pull/109),
  [`89ebe5d`](https://github.com/jentic/jentic-openapi-tools/commit/89ebe5d2f2ca9b2718afec1dce443df9b88b1be6))

- **datamodels**: Provide initial impl of true low level datamodel
  ([`8475a90`](https://github.com/jentic/jentic-openapi-tools/commit/8475a90a791ea57a63e3fb4e55884abd2037cd05))

- **transformer**: Add `count_references` utility to analyze reference types
  ([`369ba46`](https://github.com/jentic/jentic-openapi-tools/commit/369ba46ea46642a413f9573b355095b24e7c7df1))

### Refactoring

- **datamodels**: Handle specification extensions consistently
  ([#108](https://github.com/jentic/jentic-openapi-tools/pull/108),
  [`3e18cf4`](https://github.com/jentic/jentic-openapi-tools/commit/3e18cf482da2d7795131fb249acf7ed9ef2c8263))


## v1.0.0-alpha.12 (2025-10-29)

### Features

- **parser**: Add sort_keys option to json_dumps
  ([#104](https://github.com/jentic/jentic-openapi-tools/pull/104),
  [`f4ee13d`](https://github.com/jentic/jentic-openapi-tools/commit/f4ee13d255b5a57bdc132d508b2f1e9316efea53))


## v1.0.0-alpha.11 (2025-10-23)

### Continuous Integration

- **release**: Re-enable release checks (tests/lint/types)
  ([#97](https://github.com/jentic/jentic-openapi-tools/pull/97),
  [`2229d75`](https://github.com/jentic/jentic-openapi-tools/commit/2229d75822fae94b73d1f8d80b0fd8fabe2d4853))

### Documentation

- **CHANGELOG**: Align changelog with GitHub releases
  ([#98](https://github.com/jentic/jentic-openapi-tools/pull/98),
  [`f84e80a`](https://github.com/jentic/jentic-openapi-tools/commit/f84e80ad14d765f23168d46ae8ccf651f83de38c))

### Refactoring

- **common**: Consolidate URI & URL predicates
  ([#99](https://github.com/jentic/jentic-openapi-tools/pull/99),
  [`9a94070`](https://github.com/jentic/jentic-openapi-tools/commit/9a94070709eac9af0ce0245a622d5f729afaee98))

### Testing

- **vaildator**: Extract http testing server into conftest
  ([#100](https://github.com/jentic/jentic-openapi-tools/pull/100),
  [`38b3975`](https://github.com/jentic/jentic-openapi-tools/commit/38b3975f8e091cc958c5499173ea5aa2cf7f81fe))


## v1.0.0-alpha.10 (2025-10-23)

- initial release of `jentic-openapi-validator-spectral` pypi package

## v1.0.0-alpha.9 (2025-10-23)

- initial release of `jentic-openapi-validator-redocly` pypi package

## v1.0.0-alpha.8 (2025-10-23)

### Continuous Integration

- **release**: Generate artifact attestations for release artifacts ([#95](https://github.com/jentic/jentic-openapi-tools/pull/95), [`20c95c1`](https://github.com/jentic/jentic-openapi-tools/commit/20c95c15a449238c995024758febe9d7ad990c23))


## v1.0.0-alpha.7 (2025-10-22)

- initial release of `jentic-openapi-validator` pypi package

## v1.0.0-alpha.6 (2025-10-22)

- initial release of `jentic-openapi-traverse` pypi package

## v1.0.0-alpha.5 (2025-10-22)

- initial release of `jentic-openapi-transformer` pypi package


## v1.0.0-alpha.4 (2025-10-22)

- failed initial release of `jentic-openapi-transformer` pypi package

## v1.0.0-alpha.3 (2025-10-22)

- initial release of `jentic-openapi-parser` pypi package

## v1.0.0-alpha.2 (2025-10-22)

- initial release of `jentic-openapi-datamodels` pypi package


## v1.0.0-alpha.1 (2025-10-22)

- initial release of `jentic-openapi-common` pypi package

### Documentation

- **SECURITY**: Provide currently supported version range ([#93](https://github.com/jentic/jentic-openapi-tools/pull/93), [`6662893`](https://github.com/jentic/jentic-openapi-tools/commit/6662893795efaecc17c32aeac8983125e10ccfdc))


## v1.0.0 (2025-10-21)

- Initial Release
