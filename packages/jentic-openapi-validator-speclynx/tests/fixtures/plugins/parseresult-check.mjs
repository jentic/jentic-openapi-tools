/**
 * Test plugin that verifies parseResult is available in the toolbox.
 *
 * This plugin emits a diagnostic if parseResult is missing or doesn't contain
 * expected properties, helping catch regressions in toolbox wiring.
 */

export default (toolbox) => {
    const {diagnostics, deps, parseResult} = toolbox;
    const {DiagnosticSeverity} = deps['vscode-languageserver-types'];

    return {
        visitor: {
            InfoElement() {
                // Verify parseResult is available
                if (!parseResult) {
                    diagnostics.push({
                        severity: DiagnosticSeverity.Error,
                        message: 'toolbox.parseResult is missing',
                        code: 'missing-parseresult',
                        range: {
                            start: {line: 0, character: 0},
                            end: {line: 0, character: 0}
                        },
                        data: {path: []}
                    });
                    return;
                }

                // For valid OpenAPI 3.x documents, parseResult.api should exist
                if (parseResult.api) {
                    diagnostics.push({
                        severity: DiagnosticSeverity.Information,
                        message: 'parseResult.api is available',
                        code: 'parseresult-api-available',
                        range: {
                            start: {line: 0, character: 0},
                            end: {line: 0, character: 0}
                        },
                        data: {path: []}
                    });
                }
            }
        }
    };
};
