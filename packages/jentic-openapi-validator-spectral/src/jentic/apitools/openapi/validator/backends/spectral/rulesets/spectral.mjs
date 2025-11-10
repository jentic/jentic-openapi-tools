/**
 * JavaScript Ruleset Format: https://docs.stoplight.io/docs/spectral/aa15cdee143a1-java-script-ruleset-format
 */
import { oas3 } from '@stoplight/spectral-formats';
import { oasExample } from '@stoplight/spectral-rulesets/dist/oas/functions/index.js';
import oasRuleset from '@stoplight/spectral-rulesets/dist/oas/index.js';

// Custom wrapper around oasExample that skips XML-related examples
const oasExampleNonXml = (targetVal, opts, context) => {
  const path = context.path || [];
  const pathString = path.join('.');

  // Case 1: Media Type Objects - filter by media type in path
  // Path format: paths./station-timetables.get.responses[200].content.application/xml.examples
  // Matches patterns like: .content.application/xml. or .content.image/svg+xml.
  if (pathString.match(/\.content\.[^.]*(\/xml|\+xml)\b/i)) {
    return [];
  }

  // Case 2 & 3: Header/Parameter Objects - check if their schema has xml property
  // Path format: paths./stations.get.parameters[0].schema or paths./.headers.X-Custom.schema
  // The targetVal is the object with schema and example/examples
  if (targetVal && targetVal.schema && targetVal.schema.xml) {
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
          schemaField: 'schema',
          oasVersion: 3,
          type: 'media'
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
        '$.components.schemas..[?(@property !== \'properties\' && @ && (@.example !== void 0 || @.default !== void 0) && (@.enum || @.type || @.format || @.$ref || @.properties || @.items) && !@.xml)]',
        '$..content..[?(@property !== \'properties\' && @ && (@.example !== void 0 || @.default !== void 0) && (@.enum || @.type || @.format || @.$ref || @.properties || @.items) && !@.xml)]',
        '$..headers..[?(@property !== \'properties\' && @ && (@.example !== void 0 || @.default !== void 0) && (@.enum || @.type || @.format || @.$ref || @.properties || @.items) && !@.xml)]',
        '$..parameters..[?(@property !== \'properties\' && @ && (@.example !== void 0 || @.default !== void 0) && (@.enum || @.type || @.format || @.$ref || @.properties || @.items) && !@.xml)]'
      ],
      then: {
        function: oasExample,
        functionOptions: {
          schemaField: '$',
          oasVersion: 3,
          type: 'schema'
        }
      }
    }
  }
};
