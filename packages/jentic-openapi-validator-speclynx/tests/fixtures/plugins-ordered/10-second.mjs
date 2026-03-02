/**
 * Test plugin: should load second (numeric prefix 10).
 */
export default (toolbox) => {
    const {diagnostics, deps} = toolbox;
    const {DiagnosticSeverity} = deps['vscode-languageserver-types'];

    return {
        visitor: {
            InfoElement() {
                diagnostics.push({
                    severity: DiagnosticSeverity.Information,
                    message: 'order:10-second',
                    code: 'plugin-order',
                    range: {start: {line: 0, character: 0}, end: {line: 0, character: 0}},
                    data: {path: []}
                });
            }
        }
    };
};
