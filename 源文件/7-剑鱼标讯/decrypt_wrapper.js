const fs = require("fs");
const path = require("path");

const jsCode = fs.readFileSync(path.join(__dirname, "JianYv-decrypt.js"), "utf-8");
eval(jsCode);

let inputData = "";
process.stdin.on("data", chunk => inputData += chunk);
process.stdin.on("end", () => {
    const { encrypt_text, secret_key } = JSON.parse(inputData);
    get_decrypt_res(encrypt_text, secret_key).then(result => {
        process.stdout.write(JSON.stringify(result));
    }).catch(err => {
        process.stderr.write(err.message);
        process.exit(1);
    });
});
