#!/usr/bin/env node
import {promisify} from 'node:util';
import {readdir, writeFile} from 'node:fs/promises';
import path from 'node:path';
import {pathToFileURL, fileURLToPath} from 'node:url';
import {Command} from 'commander';
import {DiagnosticSeverity} from 'vscode-languageserver-types';
import {dispatchRefractorPlugins} from '@speclynx/apidom-core';
import {parse, options} from '@speclynx/apidom-reference';
import FileResolver from '@speclynx/apidom-reference/resolve/resolvers/file';
import HTTPResolverAxios from '@speclynx/apidom-reference/resolve/resolvers/http-axios';
import OpenAPI3_0ResolveStrategy from '@speclynx/apidom-reference/resolve/strategies/openapi-3-0';
import OpenAPI3_1ResolveStrategy from '@speclynx/apidom-reference/resolve/strategies/openapi-3-1';
import OpenAPI3_0DereferenceStrategy from '@speclynx/apidom-reference/dereference/strategies/openapi-3-0';
import OpenAPI3_1DereferenceStrategy from '@speclynx/apidom-reference/dereference/strategies/openapi-3-1';
import OpenAPIJSON3_0Parser from '@speclynx/apidom-reference/parse/parsers/openapi-json-3-0';
import OpenAPIYAML3_0Parser from '@speclynx/apidom-reference/parse/parsers/openapi-yaml-3-0';
import OpenAPIJSON3_1Parser from '@speclynx/apidom-reference/parse/parsers/openapi-json-3-1';
import OpenAPIYAML3_1Parser from '@speclynx/apidom-reference/parse/parsers/openapi-yaml-3-1';
import JSONParser from '@speclynx/apidom-reference/parse/parsers/json';
import YAMLParser from '@speclynx/apidom-reference/parse/parsers/yaml-1-2';
import BinaryParser from '@speclynx/apidom-reference/parse/parsers/binary';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Configure ApiDOM options
function configureOptions(cliOptions) {
    // Configure file allow list based on allowed-base-dir option
    let fileAllowList = ['*'];
    if (cliOptions.allowedBaseDir) {
        // Resolve to absolute path and convert to forward slashes for glob compatibility
        const absolutePath = path.resolve(cliOptions.allowedBaseDir);
        const normalizedPath = absolutePath.split(path.sep).join('/');
        fileAllowList = [`${normalizedPath}/**`];
    }

    options.resolve.resolvers = [
        new FileResolver({fileAllowList}),
        new HTTPResolverAxios({
            timeout: parseInt(cliOptions.timeout, 10),
            redirects: 5,
            withCredentials: false
        })
    ];

    options.parse.parsers = [
        new OpenAPIJSON3_0Parser({allowEmpty: true, sourceMap: true, strict: false}),
        new OpenAPIYAML3_0Parser({allowEmpty: true, sourceMap: true, strict: false}),
        new OpenAPIJSON3_1Parser({allowEmpty: true, sourceMap: true, strict: false}),
        new OpenAPIYAML3_1Parser({allowEmpty: true, sourceMap: true, strict: false}),
        new JSONParser({allowEmpty: true, sourceMap: true, strict: false}),
        new YAMLParser({allowEmpty: true, sourceMap: true, strict: false}),
        new BinaryParser({allowEmpty: true})
    ];

    options.resolve.strategies = [
        new OpenAPI3_0ResolveStrategy(),
        new OpenAPI3_1ResolveStrategy(),
    ];
    options.resolve.baseURI = cliOptions.baseUri ?? options.resolve.baseURI;

    options.dereference.strategies = [
        new OpenAPI3_0DereferenceStrategy(),
        new OpenAPI3_1DereferenceStrategy(),
    ];

    options.bundle.strategies = [];
}

// Load validation plugins
async function loadPlugins(pluginsPath) {
    const plugins = [];

    try {
        const files = await readdir(pluginsPath);
        const mjsFiles = files.filter(file => file.endsWith('.mjs'));

        for (const file of mjsFiles) {
            const filePath = path.join(pluginsPath, file);
            const fileUrl = pathToFileURL(filePath).href;
            const module = await import(fileUrl);

            if (module.default) {
                plugins.push(module.default);
            }
        }

        if (plugins.length > 0) {
            console.error(`Loaded ${plugins.length} plugin(s) from ${pluginsPath}`);
        }
    } catch (error) {
        if (error.code !== 'ENOENT') {
            console.error('Error loading plugins:', error.message);
        }
    }

    return plugins;
}

// Main validation function
async function validate(document, cliOptions) {
    configureOptions(cliOptions);

    // Always load default plugins
    const defaultPluginsPath = path.join(__dirname, 'plugins');
    const defaultPlugins = await loadPlugins(defaultPluginsPath);

    // Load custom plugins if specified and merge with defaults
    let plugins = defaultPlugins;
    if (cliOptions.plugins) {
        const customPlugins = await loadPlugins(cliOptions.plugins);
        plugins = [...defaultPlugins, ...customPlugins];
    }

    const diagnostics = [];

    // Parse the document - convert parse errors to diagnostics
    let parseResult;
    try {
        parseResult = await parse(document);
    } catch (error) {
        // Convert parse errors (e.g., empty file, invalid syntax) to diagnostics
        diagnostics.push({
            severity: DiagnosticSeverity.Error,
            message: error.message || 'Failed to parse document',
            code: 'parse-error',
            range: {start: {line: 0, character: 0}, end: {line: 0, character: 0}},
            data: {path: []}
        });
        return {valid: false, diagnostics};
    }

    // Run validation plugins
    // When parseResult.api exists, traverse it (paths are relative to document root)
    // When it doesn't exist (e.g., Swagger 2.0), traverse parseResult so ParseResultElement visitor runs
    const elementToTraverse = parseResult.api ?? parseResult;
    const dispatchRefractorPluginsAsync = promisify(dispatchRefractorPlugins);
    await dispatchRefractorPluginsAsync(elementToTraverse, plugins.map(plugin => plugin({diagnostics})));

    // Check if there are any errors or warnings
    const hasErrors = diagnostics.some(d => d.severity === DiagnosticSeverity.Error);

    // Format the result
    return {valid: !hasErrors, diagnostics};
}

// CLI setup
const program = new Command();

program
    .name('speclynx')
    .description('SpecLynx OpenAPI validator using ApiDOM')
    .version('0.1.0')
    .argument('<document>', 'OpenAPI document path or URL to validate')
    .option('-p, --plugins <path>', 'additional plugins directory path (merged with built-in plugins)')
    .option('-o, --output <file>', 'output file path (default: stdout)')
    .option('--base-uri <uri>', 'base URI for resolving relative references')
    .option('--allowed-base-dir <path>', 'restrict file resolution to this directory')
    .option('--timeout <ms>', 'HTTP timeout in milliseconds', '5000')
    .action(async (document, cliOptions) => {
        try {
            const result = await validate(document, cliOptions);

            // Format output as JSON
            const output = JSON.stringify(result.diagnostics, null, 2);

            // Write to file or stdout
            if (cliOptions.output) {
                await writeFile(cliOptions.output, output, 'utf-8');
                console.error(`Validation results written to ${cliOptions.output}`);
            } else {
                console.log(output);
            }

            // Exit with code 1 if errors or warnings found, 0 otherwise
            const exitCode = result.valid ? 0 : 1;
            process.exit(exitCode);
        } catch (error) {
            console.error('Validation error:', error.message);
            if (error.stack) {
                console.error(error.stack);
            }
            process.exit(1);
        }
    });

program.parse();
