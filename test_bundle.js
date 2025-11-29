const { parseName } = require('./dist/evoname');

const input = "Dr. Hans Müller";
console.log(`Testing bundle with input: "${input}"`);

try {
    const result = parseName(input);
    console.log("Result:", JSON.stringify(result, null, 2));

    // Basic validation
    if (result.given && result.family) {
        console.log("SUCCESS: Name parsed and returned structure.");
    } else {
        console.error("FAILURE: Result missing given/family fields.");
        process.exit(1);
    }
} catch (e) {
    console.error("ERROR:", e);
    process.exit(1);
}
