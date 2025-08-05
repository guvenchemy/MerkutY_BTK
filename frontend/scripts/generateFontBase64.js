const fs = require('fs');
const path = require('path');

const fontPath = path.join(__dirname, '../public/fonts/Roboto-Regular.ttf');
const outputPath = path.join(__dirname, '../src/components/smart/fonts/Roboto-Regular-normal.js');

// Read font file
const fontBuffer = fs.readFileSync(fontPath);
const base64Font = fontBuffer.toString('base64');

// Create output directory if it doesn't exist
const outputDir = path.dirname(outputPath);
if (!fs.existsSync(outputDir)) {
  fs.mkdirSync(outputDir, { recursive: true });
}

// Generate JavaScript file with base64 font data
const fileContent = `// Generated font file - DO NOT EDIT
export default '${base64Font}';
`;

fs.writeFileSync(outputPath, fileContent);
console.log('Font file generated successfully!'); 