/**
 * Test plugin that validates info.version is a string
 *
 * Plugin receives toolbox with:
 * - deps: External dependencies including vscode-languageserver-types, @speclynx/apidom-core,
 *   @speclynx/apidom-datamodel, @speclynx/apidom-json-path, @speclynx/apidom-json-pointer,
 *   @speclynx/apidom-traverse, and @speclynx/apidom-reference
 * - diagnostics: Array to collect validation diagnostics
 */

export default (toolbox) => {
    const {diagnostics, deps} = toolbox;
    const {DiagnosticSeverity} = deps['vscode-languageserver-types'];
    const {toValue} = deps['@speclynx/apidom-core'];

    return {
        visitor: {
            InfoElement(path) {
                const info = path.node;
                const version = info.get('version');

                if (version && typeof toValue(version) !== 'string') {
                    diagnostics.push({
                        severity: DiagnosticSeverity.Error,
                        message: 'info.version must be a string',
                        code: 'invalid-info-version-type',
                        range: getRange(version),
                        data: {path: path.getPathKeys()}
                    });
                }
            }
        }
    };
};

function getRange(element) {
    if (!element) {
        return {
            start: {line: 0, character: 0},
            end: {line: 0, character: 0}
        };
    }

    return {
        start: {
            line: element.startLine ?? 0,
            character: element.startCharacter ?? 0
        },
        end: {
            line: element.endLine ?? element.startLine ?? 0,
            character: element.endCharacter ?? element.startCharacter ?? 0
        }
    };
}
