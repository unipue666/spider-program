var crypto_js = require("crypto-js");

function l(t, e) {
    return t.toString().toUpperCase() > e.toString().toUpperCase() ? 1 : t.toString().toUpperCase() == e.toString().toUpperCase() ? 0 : -1
}

function u(t) {
    for (var e = Object.keys(t).sort(l), n = "", a = 0; a < e.length; a++)
        if (void 0 !== t[e[a]])
            if (t[e[a]] && t[e[a]] instanceof Object || t[e[a]] instanceof Array) {
                var i = JSON.stringify(t[e[a]]);
                n += e[a] + i
            } else
                n += e[a] + t[e[a]];
    return n
}

// 获取请求头加密参数
function get_encrypt_header(page) {
    var timestamp = (new Date).getTime()
    var t = {
        "ts": timestamp,
        "pageNo": page,
        "pageSize": 10,
        "total": 748,
        "type": "11",
        "timeType": "0"
    }
    for (var e in t)
        "" !== t[e] && void 0 !== t[e] || delete t[e];
    var n = "B3978D054A72A7002063637CCDF6B2E5" + u(t);
    return {
        "portal-sign": crypto_js.MD5(n).toString(),
        "ts": timestamp
    }
}

// console.log(get_encrypt_header(1))


// 获取响应解密
function get_decrypt_response(encrypt_data) {
    function b(t) {
        var e = crypto_js.enc.Utf8.parse("EB444973714E4A40876CE66BE45D5930")
            , n = crypto_js.enc.Utf8.parse("B5A8904209931867")
            , a = crypto_js.AES.decrypt(t, e, {
            iv: n,
            mode: crypto_js.mode.CBC,
            padding: crypto_js.pad.Pkcs7
        });
        return a.toString(crypto_js.enc.Utf8)
    }
    decrypt_res = JSON.parse(b(encrypt_data))
    return decrypt_res
}

// var encrypt_data = "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"
// console.log(get_decrypt_response(encrypt_data))