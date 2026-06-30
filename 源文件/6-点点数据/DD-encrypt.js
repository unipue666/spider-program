var crypto = require('crypto')

function m_b(n, e, o) {
    var c = "";
    var l = crypto.createDecipheriv("aes-128-cbc", e, o);
    return c += l.update(n, "hex", "utf8"),
        c += l.final("utf8")
}

function y_a(n, path, e, r) {
    var s = e.s
        , c = e.k
        , d = e.l
        , h = e.d
        , y = e.sort
        , w = e.num
        , _ = function (content, t, n) {
        for (var a = Array.from(content), e = Array.from(t), r = a.length, o = e.length, c = String.fromCodePoint, i = 0; i < r; i++)
            a[i] = c(a[i].codePointAt(0) ^ e[(i + n) % o].codePointAt(0));
        return a.join("")
    }(function (s, t, path, n) {
        return [s, t, n, path].join("(&&)")
    }(function (t, n) {
        var e = t;
        var r = [];
        for (var c in e)
            Array.isArray(e[c]) && "get" === n && (e[c] = e[c].join("")),
            "post" === n && (f()(e[c]) || o()(e[c])) && (e[c] = JSON.stringify(e[c])),
                r.push(e[c]);
        return r.sort(),
            r.join("")
    }(n, r), parseInt((new Date).getTime() / 1e3) - 655876800 - h, path, y), m_b(s, c, d), w);
    return btoa(_)
}

function get_encrypt_k(page) {
    var timestamp = parseInt(new Date().getTime() / 1000)
    var r = {
        "market_id": 1,
        "genre_id": 0,
        "country_id": 75,
        "device_id": 1,
        "page": page,
        "time": timestamp,
        "rank_type": 4,
        "brand_id": 2
    };
    var path = "/v1/rank"
    o = y_a(r, path, {
        s: "1c475deae1df66347b0a757d8861e31f",
        k: "9836828ceb09268d",
        l: "8bca24d7845d4a97",
        d: 3,
        sort: "dd",
        num: 10
    }, "get");
    r.k = o
    return {
        "params": r
    }
}


// console.log(get_encrypt_k(2))