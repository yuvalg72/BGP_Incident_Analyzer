const crypto = require("node:crypto");
const path = require("node:path");
const sharp = require("sharp");

const root = path.resolve(__dirname, "..");
const generatedDir = process.argv[2];
const diagrams = ["architecture", "analysis-flow"];

if (!generatedDir) {
  process.stderr.write("Usage: node scripts/compare-diagrams.js <generated-directory>\n");
  process.exit(2);
}

async function normalizedPixels(file) {
  const { data, info } = await sharp(file)
    .flatten({ background: "#ffffff" })
    .resize(140, 76, { fit: "fill" })
    .greyscale()
    .blur(0.5)
    .raw()
    .toBuffer({ resolveWithObject: true });
  return {
    width: info.width,
    height: info.height,
    channels: info.channels,
    data,
  };
}

Promise.all(diagrams.map(async (name) => {
  const committed = await normalizedPixels(path.join(root, "docs", "images", `${name}.png`));
  const generated = await normalizedPixels(path.join(generatedDir, `${name}.png`));
  if (committed.width !== generated.width || committed.height !== generated.height || committed.channels !== generated.channels) {
    throw new Error(`${name}.png dimensions do not match its generated render`);
  }
  let difference = 0;
  for (let index = 0; index < committed.data.length; index += 1) {
    difference += Math.abs(committed.data[index] - generated.data[index]);
  }
  const meanDifference = difference / committed.data.length;
  const threshold = 8;
  if (meanDifference > threshold) {
    throw new Error(`${name}.png differs materially from its SVG source (mean difference ${meanDifference.toFixed(3)} > ${threshold})`);
  }
  const digest = crypto.createHash("sha256").update(generated.data).digest("hex").slice(0, 12);
  process.stdout.write(`Verified ${name}.png (mean difference ${meanDifference.toFixed(3)}, render ${digest})\n`);
})).catch((error) => {
  process.stderr.write(`${error.stack || error}\n`);
  process.exitCode = 1;
});
