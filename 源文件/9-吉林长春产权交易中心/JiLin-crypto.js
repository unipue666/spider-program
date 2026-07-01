var obj_2 = {
    "codeStr": "",
    "pubPass": "BX1o65CoobwcDP33iQW6ld1OyIPsNzF1",
    "pubPassNum": [
        66,
        88,
        49,
        111,
        54,
        53,
        67,
        111,
        111,
        98,
        119,
        99,
        68,
        80,
        51,
        51,
        105,
        81,
        87,
        54,
        108,
        100,
        49,
        79,
        121,
        73,
        80,
        115,
        78,
        122,
        70,
        49
    ],
    "publicKey": ""
}

function random_1(t, e) {
    return void 0 === t && (t = 0),
    void 0 === e && (e = 1e4),
        Math.floor(Math.random() * (e - t) + t)
}

function random_str(t) {
    for (var e = [], n = 0; n < t; n++)
        e.push(random_1(0, 35).toString(36));
    return e.join("")
}

function stringChangeASCIINumberArrs(t) {
    for (var e = [], n = 0; n < t.length; n++)
        e.push(t.charCodeAt(n));
    return e
}

function encryptCode(t) {
    for (var e = encodeURI(t), n = [], i = 0, r = "", o = random_1(16, 32), a = random_str(o), c = stringChangeASCIINumberArrs(a), s = 0, u = 0, l = 0, h = 0; h < e.length; h++)
        i = e.charCodeAt(h),
        s == obj_2.pubPassNum.length && (s = 0),
            i += obj_2.pubPassNum[s],
            s++,
        u == c.length && (u = 0),
            i += c[u],
            u++,
            l += i,
        l > 65535 && (l -= 65535),
            r = i.toString(36),
            r = ("00" + r).substr(-2, 2),
        1 == r.length && (r = "0" + r),
            n.push(r);
    var f = "";
    return f = l.toString(36),
        f = ("0000" + r).substr(-4, 4),
        n.unshift(a),
        n.unshift(o.toString(36)),
        n.unshift(f),
        n.join("")
}

function get_encrypt_data(data) {
    var s = JSON.stringify(data)
    e = JSON.stringify(s)
    return {
        encrypt_data: encryptCode(e)
    }
}


// 响应数据解密
function decryptCode(t) {
    var e = ""
        , n = 0
        , i = ""
        , r = []
        , o = []
        , a = 0
        , c = 0;
    e = t.substr(4, 1),
        n = parseInt(e, 36),
        i = t.substr(5, n),
        r = stringChangeASCIINumberArrs(i),
        e = t.substr(5 + n, t.length - 5 - n);
    for (var s = "", u = 0, l = 0, h = 0; h < e.length / 2; h++)
        s = e.substr(l, 2),
            l += 2,
            u = parseInt(s, 36),
        c == r.length && (c = 0),
            u -= r[c],
            c++,
        a == obj_2.pubPass.length && (a = 0),
            u -= obj_2.pubPassNum[a],
            a++,
            s = String.fromCharCode(u),
            o.push(s);
    return e = o.join(""),
        e = decodeURI(e),
        e
}
function get_decrypt_response(encrypt_data) {
    var e = JSON.parse(decryptCode(encrypt_data))
    return e.results["0"].args["0"].list
}

