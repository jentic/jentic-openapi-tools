# CHANGELOG

<!-- version list -->

## v1.0.0-alpha.22 (2025-11-20)

### Bug Fixes

- **datamodels**: Use patterned fields properly
  ([#158](https://github.com/jentic/jentic-openapi-tools/pull/158),
  [`df0eb6f`](https://github.com/jentic/jentic-openapi-tools/commit/df0eb6f21458136b542dd1dc9767f71154004cc4))

- **redocly-validator**: Collect diagnostics to temp output file
  ([#161](https://github.com/jentic/jentic-openapi-tools/pull/161),
  [`0bda9e4`](https://github.com/jentic/jentic-openapi-tools/commit/0bda9e418b141af668844a4d088a1823b0c7aac0))

- **validator-spectral**: Collect diagnostics to temp output file
  ([#159](https://github.com/jentic/jentic-openapi-tools/pull/159),
  [`5e6f3f0`](https://github.com/jentic/jentic-openapi-tools/commit/5e6f3f0d2a24298805f9e345e504fa2666eae458))

### Features

- **common**: Allow to pass custom stdout/stderr to run_subprocess
  ([#160](https://github.com/jentic/jentic-openapi-tools/pull/160),
  [`d391c96`](https://github.com/jentic/jentic-openapi-tools/commit/d391c96d1522300979a8cfe50291299e6d510596))

- **validator-redocly**: Add support for custom error handling
  ([`51d65c7`](https://github.com/jentic/jentic-openapi-tools/commit/51d65c759e504cecf81a8dce1d14a831dc269f05))

- **validator-spectral**: Add support for custom error handling
  ([`c9a1641`](https://github.com/jentic/jentic-openapi-tools/commit/c9a16419846e125de371eeb7d009ce2c362e1aa8))


## v1.0.0-alpha.21 (2025-11-19)

### Chores

- **deps**: Resolve security issues in npm deps
  ([#154](https://github.com/jentic/jentic-openapi-tools/pull/154),
  [`49f65b8`](https://github.com/jentic/jentic-openapi-tools/commit/49f65b82f7ed18f88bc1147945dbe12f82305dcd))

### Features

- **common**: Add OpenAPI version detection capabilities
  ([#155](https://github.com/jentic/jentic-openapi-tools/pull/155),
  [`94ae710`](https://github.com/jentic/jentic-openapi-tools/commit/94ae710f1aeb3b6d0e8ebf11e5044cc6e6c835b1))

- **parser**: Add datamodel-low parser backend
  ([#156](https://github.com/jentic/jentic-openapi-tools/pull/156),
  [`3d0a5a2`](https://github.com/jentic/jentic-openapi-tools/commit/3d0a5a2b528bd6fded7bc913c218b591e4d260db))

### Refactoring

- **parser**: Use composition instead of inheritance for ruamel-ast parser
  ([#153](https://github.com/jentic/jentic-openapi-tools/pull/153),
  [`1ac0429`](https://github.com/jentic/jentic-openapi-tools/commit/1ac042902c78dab05a1cd9f01f79994bfe325be7))


## v1.0.0-alpha.20 (2025-11-18)

### Features

- **parser**: Add ruamel-ast parser backend
  ([#152](https://github.com/jentic/jentic-openapi-tools/pull/152),
  [`8e82ce3`](https://github.com/jentic/jentic-openapi-tools/commit/8e82ce3139a79c300bf445312c0c64263cbd57d8))


## v1.0.0-alpha.19 (2025-11-18)

### Bug Fixes

- **datamodels**: Fix unnecessary nesting of sources
  ([#130](https://github.com/jentic/jentic-openapi-tools/pull/130),
  [`529520e`](https://github.com/jentic/jentic-openapi-tools/commit/529520ee2a2d55e4ebdb16333c7ad265a1262903))

### Chores

- **deps**: Address js-yaml prototype pollution vulnerability
  ([#142](https://github.com/jentic/jentic-openapi-tools/pull/142),
  [`c2359eb`](https://github.com/jentic/jentic-openapi-tools/commit/c2359ebff9ee2ef7683d5fc7b0b116dca29390ce))

### Documentation

- **datamodels**: Update README to focus on OpenAPI30 main use case
  ([#150](https://github.com/jentic/jentic-openapi-tools/pull/150),
  [`836d9e5`](https://github.com/jentic/jentic-openapi-tools/commit/836d9e55d602aa119c91c9440e342a2d8692cab0))

### Features

- **dataclasses**: Create public API for low.v30 datamodels
  ([#147](https://github.com/jentic/jentic-openapi-tools/pull/147),
  [`b7a01bc`](https://github.com/jentic/jentic-openapi-tools/commit/b7a01bc15798c3e293579257aa97a5b7f1700981))

- **datamodels**: Add low model for Callback spec object
  ([#138](https://github.com/jentic/jentic-openapi-tools/pull/138),
  [`229e35b`](https://github.com/jentic/jentic-openapi-tools/commit/229e35b114c9a79eb7a6cfb592920438e6565340))

- **datamodels**: Add low model for Components spec object
  ([#144](https://github.com/jentic/jentic-openapi-tools/pull/144),
  [`d4d34ce`](https://github.com/jentic/jentic-openapi-tools/commit/d4d34cef1e1e88e64bcaac4ee12724e4e0f4d788))

- **datamodels**: Add low model for Encoding spec object
  ([#132](https://github.com/jentic/jentic-openapi-tools/pull/132),
  [`ba51293`](https://github.com/jentic/jentic-openapi-tools/commit/ba5129350689613424a8892cb0e4169413b46270))

- **datamodels**: Add low model for Example spec object
  ([#128](https://github.com/jentic/jentic-openapi-tools/pull/128),
  [`aff596b`](https://github.com/jentic/jentic-openapi-tools/commit/aff596b4011f35517a561511a705f73b6d81eab4))

- **datamodels**: Add low model for Header spec object
  ([#131](https://github.com/jentic/jentic-openapi-tools/pull/131),
  [`e060054`](https://github.com/jentic/jentic-openapi-tools/commit/e06005491a27aa19cc000c4cd866e1b138b64d31))

- **datamodels**: Add low model for Link spec object
  ([#129](https://github.com/jentic/jentic-openapi-tools/pull/129),
  [`b51f971`](https://github.com/jentic/jentic-openapi-tools/commit/b51f97183d4e63fc2b1e389520974d0cf0fe4e70))

- **datamodels**: Add low model for Media Type spec object
  ([#133](https://github.com/jentic/jentic-openapi-tools/pull/133),
  [`37a4235`](https://github.com/jentic/jentic-openapi-tools/commit/37a42352de31050b9a3b21867af0257523274227))

- **datamodels**: Add low model for OpenAPI 3.0.x spec object
  ([#146](https://github.com/jentic/jentic-openapi-tools/pull/146),
  [`f9a15dc`](https://github.com/jentic/jentic-openapi-tools/commit/f9a15dc773d5e68615e3646df8531dd11d2c4284))

- **datamodels**: Add low model for Operation spec object
  ([#139](https://github.com/jentic/jentic-openapi-tools/pull/139),
  [`759dd3f`](https://github.com/jentic/jentic-openapi-tools/commit/759dd3fe6f02d9e710a01da817815cf5469b126d))

- **datamodels**: Add low model for Parameter spec object
  ([#137](https://github.com/jentic/jentic-openapi-tools/pull/137),
  [`bb5463e`](https://github.com/jentic/jentic-openapi-tools/commit/bb5463e1d338613d4ab72f5dbbd7646a2adcff74))

- **datamodels**: Add low model for Path Item spec object
  ([#140](https://github.com/jentic/jentic-openapi-tools/pull/140),
  [`54de341`](https://github.com/jentic/jentic-openapi-tools/commit/54de34112bebb63a630bad64da7f80e4499b8dbf))

- **datamodels**: Add low model for Paths spec object
  ([#143](https://github.com/jentic/jentic-openapi-tools/pull/143),
  [`e149667`](https://github.com/jentic/jentic-openapi-tools/commit/e149667a74f530d20f17836d0ecf4625ae1214da))

- **datamodels**: Add low model for Request Body spec object
  ([#135](https://github.com/jentic/jentic-openapi-tools/pull/135),
  [`de24443`](https://github.com/jentic/jentic-openapi-tools/commit/de244431379cf91b4eeb9d30b9996ba227639edb))

- **datamodels**: Add low model for Response spec object
  ([#134](https://github.com/jentic/jentic-openapi-tools/pull/134),
  [`70591f8`](https://github.com/jentic/jentic-openapi-tools/commit/70591f8146ee70bc96e55b75f311e36aab8fc2f5))

- **datamodels**: Add low model for Responses spec object
  ([#136](https://github.com/jentic/jentic-openapi-tools/pull/136),
  [`c009423`](https://github.com/jentic/jentic-openapi-tools/commit/c009423d20cb62e48dc2c38e930f42952a68521d))

- **datamodels**: Add low model for Server spec object
  ([#126](https://github.com/jentic/jentic-openapi-tools/pull/126),
  [`3781989`](https://github.com/jentic/jentic-openapi-tools/commit/3781989dfef61cfbc3dbaf51573ce57ec619236e))

- **datamodels**: Add OpenAPI 3.1.x datamodel
  ([#151](https://github.com/jentic/jentic-openapi-tools/pull/151),
  [`900eea1`](https://github.com/jentic/jentic-openapi-tools/commit/900eea1960fd67d1a459d93fedb1b9451fe69b30))

### Refactoring

- **datamodels**: Apply DRY principle
  ([#141](https://github.com/jentic/jentic-openapi-tools/pull/141),
  [`403a6d3`](https://github.com/jentic/jentic-openapi-tools/commit/403a6d37611fe8f8c8686cc550487760bc28f3c9))

- **datamodels**: Make model builder v30 specific
  ([#149](https://github.com/jentic/jentic-openapi-tools/pull/149),
  [`4c34a5c`](https://github.com/jentic/jentic-openapi-tools/commit/4c34a5c22e4033c8651fa3af37438cae28763e44))

- **datamodels**: Simplify building models
  ([#127](https://github.com/jentic/jentic-openapi-tools/pull/127),
  [`34cfd56`](https://github.com/jentic/jentic-openapi-tools/commit/34cfd565f5f9144b79b9070eb79429ebb1b2272f))

- **datamodels**: Use relative imports
  ([#148](https://github.com/jentic/jentic-openapi-tools/pull/148),
  [`8c66f0f`](https://github.com/jentic/jentic-openapi-tools/commit/8c66f0f1287b41280b8ed4ed5d6203d8f9a73003))


## v1.0.0-alpha.18 (2025-11-13)

### Bug Fixes

- **validator**: Report missing servers from default validator as error
  ([#125](https://github.com/jentic/jentic-openapi-tools/pull/125),
  [`89f0950`](https://github.com/jentic/jentic-openapi-tools/commit/89f09500dc11164f1e7cbdc0009f9b4a42285f51))


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
