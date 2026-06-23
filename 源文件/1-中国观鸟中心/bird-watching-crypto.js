var crypto_js = require('crypto-js');
var JSEncrypt = require("jsencrypt");

function getUuid() {
    var s = [];
    var hexDigits = "0123456789abcdef";
    for (var i = 0; i < 32; i++) {
        s[i] = hexDigits.substr(Math.floor(Math.random() * 16), 1)
    }
    s[14] = "4";
    s[19] = hexDigits.substr(s[19] & 3 | 8, 1);
    s[8] = s[13] = s[18] = s[23];
    var uuid = s.join("");
    return uuid
}

// 获取加密参数
function get_encrypt(page) {
    var paramPublicKey = "MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQCvxXa98E1uWXnBzXkS2yHUfnBM6n3PCwLdfIox03T91joBvjtoDqiQ5x3tTOfpHs3LtiqMMEafls6b0YWtgB1dse1W5m+FpeusVkCOkQxB4SZDH6tuerIknnmB/Hsq5wgEkIvO5Pff9biig6AyoAkdWpSek/1/B7zYIepYY0lxKQIDAQAB";
    var encrypt = new JSEncrypt();
    encrypt.setPublicKey(paramPublicKey);
    var data = `{"limit":"20","page":"${page}"}`
    var timestamp = Date.parse(new Date);
    var requestId = getUuid();
    var sign = crypto_js.MD5(data + requestId + timestamp).toString();
    var encrypt_data = encrypt.encrypt(data)

    return {
        "timestamp": timestamp,
        "requestId": requestId,
        "sign": sign,
        "data": encrypt_data
    }
}

// console.log(get_encrypt(3))


// 响应解密
function get_decrypt_data(encrypt_data) {
    var key = crypto_js['enc']["Utf8"]["parse"]("C8EB5514AF5ADDB94B2207B08C66601C")
        , iv = crypto_js["enc"]["Utf8"]["parse"]("55DD79C6F04E1A67");
    return crypto_js["AES"]["decrypt"](encrypt_data, key, {
        'iv': iv,
        'mode': crypto_js["mode"]['CBC'],
        'padding': crypto_js['pad']["Pkcs7"]
    })['toString'](crypto_js['enc']['Utf8']);
};

