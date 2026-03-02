/**
 * Test plugin: should load last (no numeric prefix).
 */
export default (toolbox) => {
    const {diagnostics, deps} = toolbox;
    const {DiagnosticSeverity} = deps['vscode-languageserver-types'];

    return {
        visitor: {
            InfoElement() {
                diagnostics.push({
                    severity: DiagnosticSeverity.Information,
                    message: 'order:no-prefix',
                    code: 'plugin-order',
                    range: {start: {line: 0, character: 0}, end: {line: 0, character: 0}},
                    data: {path: []}
                });
            }
        }
    };
};
