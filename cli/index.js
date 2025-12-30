#!/usr/bin/env node

/**
 * EPUB to XTC/XTCH CLI Converter
 * Converts EPUB files to Xteink e-reader format
 */

const { program } = require('commander');
const fs = require('fs');
const path = require('path');
const { loadSettings, resolveSettings, validateSettings, generateDefaultConfig } = require('./settings');
const { convertEpub, getOutputPath, cleanup } = require('./converter');

program
    .name('epub-to-xtc')
    .description('Convert EPUB files to XTC/XTCH format for Xteink e-readers')
    .version('1.0.0');

program
    .command('convert <input>')
    .description('Convert EPUB file(s) to XTC/XTCH format')
    .option('-o, --output <path>', 'Output file or directory')
    .option('-c, --config <path>', 'Path to settings JSON file')
    .option('-f, --format <format>', 'Output format: xtc (1-bit) or xtch (2-bit)')
    .action(async (input, options) => {
        try {
            // Load and resolve settings
            let settings = loadSettings(options.config);
            settings = resolveSettings(settings);

            // Override format if specified
            if (options.format) {
                settings.output.format = options.format;
            }

            // Validate settings
            const errors = validateSettings(settings);
            if (errors.length > 0) {
                console.error('Configuration errors:');
                errors.forEach(e => console.error(`  - ${e}`));
                process.exit(1);
            }

            // Resolve input path
            const inputPath = path.resolve(input);

            if (!fs.existsSync(inputPath)) {
                console.error(`Input not found: ${inputPath}`);
                process.exit(1);
            }

            const stat = fs.statSync(inputPath);

            if (stat.isDirectory()) {
                // Convert all EPUBs in directory
                await convertDirectory(inputPath, options.output, settings);
            } else if (stat.isFile() && inputPath.endsWith('.epub')) {
                // Convert single file
                await convertSingleFile(inputPath, options.output, settings);
            } else {
                console.error('Input must be an EPUB file or directory containing EPUB files');
                process.exit(1);
            }

        } catch (err) {
            console.error(`Error: ${err.message}`);
            process.exit(1);
        } finally {
            cleanup();
        }
    });

program
    .command('init')
    .description('Generate default settings.json file')
    .option('-o, --output <path>', 'Output path', 'settings.json')
    .action((options) => {
        const outputPath = path.resolve(options.output);

        if (fs.existsSync(outputPath)) {
            console.error(`File already exists: ${outputPath}`);
            process.exit(1);
        }

        fs.writeFileSync(outputPath, generateDefaultConfig());
        console.log(`Created default settings file: ${outputPath}`);
        console.log('\nImportant: Edit the file to set font.path to your TTF/OTF font file.');
    });

async function convertSingleFile(inputPath, outputPath, settings) {
    // Determine output path
    if (!outputPath) {
        const dir = path.dirname(inputPath);
        outputPath = getOutputPath(inputPath, dir, settings.output.format);
    } else if (fs.existsSync(outputPath) && fs.statSync(outputPath).isDirectory()) {
        outputPath = getOutputPath(inputPath, outputPath, settings.output.format);
    } else {
        outputPath = path.resolve(outputPath);
    }

    const filename = path.basename(inputPath);
    console.log(`Converting: ${filename}`);

    const result = await convertEpub(inputPath, outputPath, settings, (current, total) => {
        const percent = Math.round((current / total) * 100);
        process.stdout.write(`\r  Progress: ${current}/${total} pages (${percent}%)`);
    });

    console.log(`\n  Output: ${result.outputPath}`);
    console.log(`  Pages: ${result.pageCount}`);
    console.log(`  Format: ${result.format.toUpperCase()}`);
}

async function convertDirectory(inputDir, outputDir, settings) {
    // Find all EPUB files
    const files = fs.readdirSync(inputDir)
        .filter(f => f.endsWith('.epub'))
        .map(f => path.join(inputDir, f));

    if (files.length === 0) {
        console.error('No EPUB files found in directory');
        process.exit(1);
    }

    // Determine output directory
    if (!outputDir) {
        outputDir = inputDir;
    } else {
        outputDir = path.resolve(outputDir);
        if (!fs.existsSync(outputDir)) {
            fs.mkdirSync(outputDir, { recursive: true });
        }
    }

    console.log(`Converting ${files.length} EPUB file(s)...\n`);

    let successCount = 0;
    let failCount = 0;

    for (let i = 0; i < files.length; i++) {
        const inputPath = files[i];
        const filename = path.basename(inputPath);
        const outputPath = getOutputPath(inputPath, outputDir, settings.output.format);

        console.log(`[${i + 1}/${files.length}] ${filename}`);

        try {
            const result = await convertEpub(inputPath, outputPath, settings, (current, total) => {
                const percent = Math.round((current / total) * 100);
                process.stdout.write(`\r  Progress: ${current}/${total} pages (${percent}%)`);
            });

            console.log(`\n  Output: ${path.basename(result.outputPath)}`);
            console.log(`  Pages: ${result.pageCount}\n`);
            successCount++;

        } catch (err) {
            console.log(`\n  Error: ${err.message}\n`);
            failCount++;
        }
    }

    console.log(`\nConversion complete: ${successCount} succeeded, ${failCount} failed`);
}

program.parse();
