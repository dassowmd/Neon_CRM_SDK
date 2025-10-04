#!/usr/bin/env node

// Script to use the configured Swagger-MCP server
import { spawn } from 'child_process';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __dirname = dirname(fileURLToPath(import.meta.url));

function sendMCPRequest(method, params = {}) {
    return new Promise((resolve, reject) => {
        const mcpServer = spawn('node', [join(__dirname, 'Swagger-MCP/build/index.js')]);

        let responseData = '';
        let errorData = '';

        mcpServer.stdout.on('data', (data) => {
            responseData += data.toString();
        });

        mcpServer.stderr.on('data', (data) => {
            errorData += data.toString();
        });

        mcpServer.on('close', (code) => {
            if (code === 0) {
                try {
                    const response = JSON.parse(responseData);
                    resolve(response);
                } catch (error) {
                    resolve({ responseData, errorData });
                }
            } else {
                reject(new Error(`MCP server exited with code ${code}: ${errorData}`));
            }
        });

        // Send the MCP request
        const request = {
            jsonrpc: "2.0",
            id: 1,
            method,
            params
        };

        mcpServer.stdin.write(JSON.stringify(request) + '\n');
        mcpServer.stdin.end();
    });
}

async function main() {
    console.log('🚀 Using Swagger-MCP to work with Neon CRM API...\n');

    try {
        // Step 1: Load the Swagger definition
        console.log('📥 Step 1: Loading Neon CRM API specification...');

        const loadResult = await sendMCPRequest('tools/call', {
            name: 'getSwaggerDefinition',
            arguments: {
                url: 'https://developer.neoncrm.com/api-v2/docs/v2.10.yaml',
                saveLocation: __dirname
            }
        });

        console.log('Load Result:', loadResult);

        // Step 2: List endpoints
        console.log('\n📋 Step 2: Listing API endpoints...');

        const endpointsResult = await sendMCPRequest('tools/call', {
            name: 'listEndpoints',
            arguments: {}
        });

        console.log('Endpoints Result:', endpointsResult);

    } catch (error) {
        console.error('❌ Error:', error.message);
    }
}

main();
