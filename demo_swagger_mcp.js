#!/usr/bin/env node

// Demo script showing what Swagger-MCP can do with the Neon CRM API
import yaml from 'js-yaml';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

function generateTypeScriptInterface(schemaName, schema, allSchemas) {
    let tsInterface = `export interface ${schemaName} {\n`;

    if (schema.properties) {
        for (const [propName, propDef] of Object.entries(schema.properties)) {
            const optional = schema.required && schema.required.includes(propName) ? '' : '?';
            let typeString = mapOpenAPITypeToTS(propDef, allSchemas);

            tsInterface += `  ${propName}${optional}: ${typeString};\n`;
        }
    }

    tsInterface += '}\n';
    return tsInterface;
}

function mapOpenAPITypeToTS(propDef, allSchemas) {
    if (propDef.$ref) {
        const refName = propDef.$ref.split('/').pop();
        return refName;
    }

    switch (propDef.type) {
        case 'string':
            return propDef.enum ? `'${propDef.enum.join("' | '")}'` : 'string';
        case 'integer':
        case 'number':
            return 'number';
        case 'boolean':
            return 'boolean';
        case 'array':
            if (propDef.items) {
                const itemType = mapOpenAPITypeToTS(propDef.items, allSchemas);
                return `${itemType}[]`;
            }
            return 'any[]';
        case 'object':
            return 'any';
        default:
            return 'any';
    }
}

function extractEndpoints(spec) {
    const endpoints = [];

    for (const [path, methods] of Object.entries(spec.paths || {})) {
        for (const [method, operation] of Object.entries(methods)) {
            if (typeof operation === 'object' && operation.operationId) {
                endpoints.push({
                    path,
                    method: method.toUpperCase(),
                    operationId: operation.operationId,
                    summary: operation.summary || '',
                    description: operation.description || '',
                    tags: operation.tags || []
                });
            }
        }
    }

    return endpoints;
}

function generateEndpointSummary(endpoints) {
    const summary = {
        totalEndpoints: endpoints.length,
        byMethod: {},
        byTag: {},
        searchEndpoints: [],
        crudEndpoints: []
    };

    endpoints.forEach(ep => {
        // Count by method
        summary.byMethod[ep.method] = (summary.byMethod[ep.method] || 0) + 1;

        // Count by tag
        ep.tags.forEach(tag => {
            summary.byTag[tag] = (summary.byTag[tag] || 0) + 1;
        });

        // Identify search endpoints
        if (ep.path.includes('/search') || ep.operationId.includes('search')) {
            summary.searchEndpoints.push(`${ep.method} ${ep.path}`);
        }

        // Identify CRUD endpoints
        if (ep.method === 'GET' || ep.method === 'POST' || ep.method === 'PUT' || ep.method === 'DELETE') {
            summary.crudEndpoints.push(`${ep.method} ${ep.path}`);
        }
    });

    return summary;
}

async function main() {
    console.log('🚀 Swagger-MCP Demo: Analyzing Neon CRM API\n');

    try {
        // Load the OpenAPI spec
        const specPath = path.join(__dirname, 'neon-api-v2.10.yaml');
        const yamlContent = fs.readFileSync(specPath, 'utf8');
        const spec = yaml.load(yamlContent);

        console.log('📋 API Information:');
        console.log(`  Title: ${spec.info.title}`);
        console.log(`  Version: ${spec.info.version}`);
        console.log(`  Description: ${spec.info.description || 'N/A'}`);
        console.log();

        // Extract endpoints
        const endpoints = extractEndpoints(spec);
        console.log(`🔗 Found ${endpoints.length} total endpoints\n`);

        // Generate endpoint summary
        const summary = generateEndpointSummary(endpoints);

        console.log('📊 Endpoint Summary:');
        console.log('  By Method:');
        Object.entries(summary.byMethod).forEach(([method, count]) => {
            console.log(`    ${method}: ${count}`);
        });

        console.log('\n  By Resource Type:');
        Object.entries(summary.byTag).slice(0, 10).forEach(([tag, count]) => {
            console.log(`    ${tag}: ${count} endpoints`);
        });

        console.log(`\n🔍 Search endpoints: ${summary.searchEndpoints.length}`);
        summary.searchEndpoints.slice(0, 5).forEach(ep => {
            console.log(`    ${ep}`);
        });
        if (summary.searchEndpoints.length > 5) {
            console.log(`    ... and ${summary.searchEndpoints.length - 5} more`);
        }

        // Generate TypeScript models for key schemas
        console.log('\n🔧 Generating TypeScript Models:\n');

        const keySchemas = ['AccountApi', 'DonationApi', 'EventApi', 'VolunteerApi', 'CampaignApi'];
        const allSchemas = spec.components?.schemas || {};

        let generatedModels = '';

        keySchemas.forEach(schemaName => {
            if (allSchemas[schemaName]) {
                console.log(`✅ Generating model for: ${schemaName}`);
                const tsInterface = generateTypeScriptInterface(schemaName, allSchemas[schemaName], allSchemas);
                generatedModels += `// ${schemaName} Model\n${tsInterface}\n`;
            } else {
                console.log(`⚠️  Schema not found: ${schemaName}`);
            }
        });

        // Save generated models
        const modelsPath = path.join(__dirname, 'generated-neon-models.ts');
        fs.writeFileSync(modelsPath, generatedModels);

        console.log(`\n💾 TypeScript models saved to: ${modelsPath}`);

        // Show some example endpoints for each major resource
        console.log('\n📋 Key Resource Endpoints:');

        const resourceGroups = {
            'Accounts': endpoints.filter(ep => ep.tags.includes('Accounts')).slice(0, 3),
            'Donations': endpoints.filter(ep => ep.tags.includes('Donations')).slice(0, 3),
            'Events': endpoints.filter(ep => ep.tags.includes('Events')).slice(0, 3),
            'Volunteers': endpoints.filter(ep => ep.tags.includes('Volunteers')).slice(0, 3)
        };

        Object.entries(resourceGroups).forEach(([resource, resourceEndpoints]) => {
            if (resourceEndpoints.length > 0) {
                console.log(`\n  ${resource}:`);
                resourceEndpoints.forEach(ep => {
                    console.log(`    ${ep.method} ${ep.path} - ${ep.summary}`);
                });
            }
        });

        console.log('\n🎉 Demo completed! The Swagger-MCP server can do all this and more:');
        console.log('  ✅ Download and cache API specifications');
        console.log('  ✅ Generate complete TypeScript models');
        console.log('  ✅ Create MCP tool definitions for each endpoint');
        console.log('  ✅ Provide endpoint documentation and validation');
        console.log('\n💡 In your next Claude Code session, you\'ll have access to the full Swagger-MCP tools!');

    } catch (error) {
        console.error('❌ Error:', error.message);
    }
}

// Install js-yaml if not available
try {
    await import('js-yaml');
} catch (error) {
    console.log('Installing js-yaml dependency...');
    const { spawn } = await import('child_process');
    await new Promise((resolve, reject) => {
        const npm = spawn('npm', ['install', 'js-yaml'], { stdio: 'inherit' });
        npm.on('close', (code) => code === 0 ? resolve() : reject(new Error('Failed to install js-yaml')));
    });
}

main();
