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

import {DiagnosticSeverity, Diagnostic, Range} from 'vscode-languageserver-types';

export default ({diagnostics}) => () => ({
    visitor: {
        ParseResultElement(path) {
            const parseResult = path.node;

            if (!parseResult.api) {
                const diagnostic = Diagnostic.create(
                    Range.create(0, 0, 0, 0),
                    'Document is not recognized as a valid OpenAPI 3.x document',
                    DiagnosticSeverity.Error,
                    'invalid-openapi-document',
                    'speclynx-validator'
                );
                diagnostic.data = {path: path.getPathKeys()};
                diagnostics.push(diagnostic);
            }
        }
    }
});
