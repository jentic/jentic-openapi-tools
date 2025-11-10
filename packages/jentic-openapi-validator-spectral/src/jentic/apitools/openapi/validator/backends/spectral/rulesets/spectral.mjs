import { oas3 } from '@stoplight/spectral-formats';
import { oasExample } from '@stoplight/spectral-rulesets/dist/oas/functions/index.js';
import oasRuleset from '@stoplight/spectral-rulesets/dist/oas/index.js';

// custom wrapper around oasExample that skips XML media types
const oasExampleNonXml = (targetVal, opts, context) => {
  // Check if the path contains an XML media type
  const path = context.path || [];
  const pathString = path.join('.');

  // Skip if the path contains any XML media type (application/xml, text/xml, *+xml)
  if (pathString.match(/\/xml|[+]xml/i)) {
    return [];
  }

  // Otherwise, delegate to the original oasExample function
  return oasExample(targetVal, opts, context);
};

export default {
  extends: [oasRuleset],
  rules: {
    'oas3-schema': 'error',

    // --- MEDIA EXAMPLES ---
    // Override to skip XML media type validation using custom wrapper function
    'oas3-valid-media-example': {
      description: 'Examples must be valid against their defined schema (non-XML media only).',
      message: '{{error}}',
      severity: 'error',
      formats: [oas3],
      given: [
        '$..content..[?(@ && @.schema && (@.example !== void 0 || @.examples))]',
        '$..headers..[?(@ && @.schema && (@.example !== void 0 || @.examples))]',
        '$..parameters..[?(@ && @.schema && (@.example !== void 0 || @.examples))]',
      ],
      then: {
        function: oasExampleNonXml,
        functionOptions: {
          schemaField: "schema",
          oasVersion: 3,
          type: "media"
        }
      }
    },

    // --- SCHEMA EXAMPLES ---
    // Override to skip schemas that have an xml property at the top level
    'oas3-valid-schema-example': {
      description: 'Examples must be valid against their defined schema (skip schemas that declare XML mapping).',
      message: '{{error}}',
      severity: 'error',
      formats: [oas3],
      given: [
        "$.components.schemas..[?(@property !== 'properties' && @ && (@.example !== void 0 || @.default !== void 0) && (@.enum || @.type || @.format || @.$ref || @.properties || @.items) && !@.xml)]",
        "$..content..[?(@property !== 'properties' && @ && (@.example !== void 0 || @.default !== void 0) && (@.enum || @.type || @.format || @.$ref || @.properties || @.items) && !@.xml)]",
        "$..headers..[?(@property !== 'properties' && @ && (@.example !== void 0 || @.default !== void 0) && (@.enum || @.type || @.format || @.$ref || @.properties || @.items) && !@.xml)]",
        "$..parameters..[?(@property !== 'properties' && @ && (@.example !== void 0 || @.default !== void 0) && (@.enum || @.type || @.format || @.$ref || @.properties || @.items) && !@.xml)]"
      ],
      then: {
        function: oasExample,
        functionOptions: {
          schemaField: "$",
          oasVersion: 3,
          type: "schema"
        }
      }
    }
  }
};
