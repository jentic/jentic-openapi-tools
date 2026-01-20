/**
 * Default plugin that validates the document is a recognized OpenAPI 3.x document.
 *
 * This plugin checks if the parsed result contains a valid OpenAPI API element,
 * which indicates the document was successfully recognized as OpenAPI 3.0 or 3.1.
 *
 * Note: This visitor is only called when traversing parseResult (invalid documents).
 * When traversing parseResult.api (valid documents), ParseResultElement is not visited.
 *
 * @param {Object} context - Plugin context
 * @param {Array} context.diagnostics - Array to collect validation diagnostics
 */

import {DiagnosticSeverity} from 'vscode-languageserver-types';

export default ({diagnostics}) => () => ({
    visitor: {
        ParseResultElement(path) {
            const parseResult = path.node;

            if (!parseResult.api) {
                diagnostics.push({
                    severity: DiagnosticSeverity.Error,
                    message: 'Document is not recognized as a valid OpenAPI 3.x document',
                    code: 'invalid-openapi-document',
                    range: {
                        start: {line: 0, character: 0},
                        end: {line: 0, character: 0}
                    },
                    data: {path: path.getPathKeys()}
                });
            }
        }
    }
});
