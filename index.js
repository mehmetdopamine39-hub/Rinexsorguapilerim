const express = require('express');
const axios = require('axios');
const cors = require('cors');
const crypto = require('crypto');
const app = express();
const PORT = process.env.PORT || 3000;

// Middleware
app.use(cors());
app.use(express.json());

// ============================================
// Cloudflare Korumasını Aşan İstek Fonksiyonu
// ============================================
async function fetchWithCF(url, options = {}) {
    const defaultHeaders = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': '*/*',
        'Accept-Language': 'tr-TR,tr;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Cache-Control': 'no-cache',
        'Pragma': 'no-cache',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-origin'
    };

    try {
        // İlk istek - cookie almak için
        const response = await axios.get(url, {
            headers: { ...defaultHeaders, ...options.headers },
            timeout: 30000,
            maxRedirects: 5,
            validateStatus: status => true // Tüm durum kodlarını kabul et
        });

        // Eğer JavaScript challenge varsa (__test cookie)
        if (response.data && response.data.includes('__test')) {
            console.log('🔐 Cloudflare challenge tespit edildi, çözülüyor...');
            
            // Cookie'yi al
            const cookies = response.headers['set-cookie'] || [];
            let testCookie = cookies.find(c => c.includes('__test='));
            
            if (testCookie) {
                // Cookie'yi çıkart
                const cookieValue = testCookie.split(';')[0];
                
                // İkinci istek - cookie ile
                const finalResponse = await axios.get(url, {
                    headers: {
                        ...defaultHeaders,
                        ...options.headers,
                        'Cookie': cookieValue
                    },
                    timeout: 30000
                });
                
                return finalResponse;
            }
        }
        
        return response;
    } catch (error) {
        console.error('Fetch hatası:', error.message);
        throw error;
    }
}

// ============================================
// 1. IBAN API - Cloudflare korumasını aşar
// ============================================
app.get('/api/iban', async (req, res) => {
    try {
        const { iban } = req.query;
        if (!iban) {
            return res.status(400).json({
                error: 'IBAN parametresi gereklidir',
                example: '/api/iban?iban=TR280006256953335759003718'
            });
        }

        const targetUrl = `https://rinexibansorguapi.rf.gd/api.php?iban=${iban}`;
        
        const response = await fetchWithCF(targetUrl, {
            headers: {
                'Origin': 'https://rinexibansorguapi.rf.gd',
                'Referer': 'https://rinexibansorguapi.rf.gd/'
            }
        });

        // JSON ise formatla, değilse ham gönder
        try {
            const jsonData = JSON.parse(response.data);
            res.json({
                success: true,
                data: jsonData,
                source: 'rinexibansorguapi.rf.gd'
            });
        } catch {
            res.set('Content-Type', 'text/plain');
            res.send(response.data);
        }

    } catch (error) {
        console.error('IBAN API Hatası:', error.message);
        res.status(500).json({
            success: false,
            error: 'IBAN sorgulama hatası',
            detail: error.message
        });
    }
});

// ============================================
// 2. Plaka API
// ============================================
app.get('/api/plaka', async (req, res) => {
    try {
        const { q } = req.query;
        if (!q) {
            return res.status(400).json({
                error: 'q parametresi gereklidir',
                example: '/api/plaka?q=34KG4978'
            });
        }

        const response = await fetchWithCF(
            `https://rinexplakasorguapi.gt.tc/api/plaka.php?endpoint=ara&q=${encodeURIComponent(q)}`,
            {
                headers: {
                    'Origin': 'https://rinexplakasorguapi.gt.tc',
                    'Referer': 'https://rinexplakasorguapi.gt.tc/'
                }
            }
        );

        try {
            const jsonData = JSON.parse(response.data);
            res.json({
                success: true,
                data: jsonData,
                source: 'rinexplakasorguapi.gt.tc'
            });
        } catch {
            res.set('Content-Type', 'text/plain');
            res.send(response.data);
        }

    } catch (error) {
        console.error('Plaka API Hatası:', error.message);
        res.status(500).json({
            success: false,
            error: 'Plaka sorgulama hatası',
            detail: error.message
        });
    }
});

// ============================================
// 3. Papara API
// ============================================
app.get('/api/papara', async (req, res) => {
    try {
        const { id, name } = req.query;
        
        if (!id && !name) {
            return res.status(400).json({
                error: 'id veya name parametresi gereklidir',
                example: '/api/papara?id=1354693996'
            });
        }

        let url = 'http://rinexpaparasorguapi.rf.gd/api/papara.php';
        if (id) {
            url += `?id=${id}`;
        } else if (name) {
            url += `?name=${encodeURIComponent(name)}`;
        }

        const response = await fetchWithCF(url, {
            headers: {
                'Origin': 'http://rinexpaparasorguapi.rf.gd',
                'Referer': 'http://rinexpaparasorguapi.rf.gd/'
            }
        });

        try {
            const jsonData = JSON.parse(response.data);
            res.json({
                success: true,
                data: jsonData,
                source: 'rinexpaparasorguapi.rf.gd'
            });
        } catch {
            res.set('Content-Type', 'text/plain');
            res.send(response.data);
        }

    } catch (error) {
        console.error('Papara API Hatası:', error.message);
        res.status(500).json({
            success: false,
            error: 'Papara sorgulama hatası',
            detail: error.message
        });
    }
});

// ============================================
// 4. Seçmen API
// ============================================
app.get('/api/secmen', async (req, res) => {
    try {
        const { action, tc, ad, soyad } = req.query;
        
        if (!action) {
            return res.status(400).json({
                error: 'action parametresi gereklidir (tc veya adsoyad)',
                example: '/api/secmen?action=tc&tc=18445070762'
            });
        }

        let url = `https://rinexsecmensorguapu.gt.tc/api/secmen.php?action=${action}`;
        
        if (action === 'tc') {
            if (!tc) {
                return res.status(400).json({ error: 'tc parametresi gereklidir' });
            }
            url += `&tc=${tc}`;
        } else if (action === 'adsoyad') {
            if (!ad || !soyad) {
                return res.status(400).json({ error: 'ad ve soyad parametreleri gereklidir' });
            }
            url += `&ad=${encodeURIComponent(ad)}&soyad=${encodeURIComponent(soyad)}`;
        } else {
            return res.status(400).json({ error: 'Geçersiz action. tc veya adsoyad kullanın' });
        }

        const response = await fetchWithCF(url, {
            headers: {
                'Origin': 'https://rinexsecmensorguapu.gt.tc',
                'Referer': 'https://rinexsecmensorguapu.gt.tc/'
            }
        });

        try {
            const jsonData = JSON.parse(response.data);
            res.json({
                success: true,
                data: jsonData,
                source: 'rinexsecmensorguapu.gt.tc'
            });
        } catch {
            res.set('Content-Type', 'text/plain');
            res.send(response.data);
        }

    } catch (error) {
        console.error('Seçmen API Hatası:', error.message);
        res.status(500).json({
            success: false,
            error: 'Seçmen sorgulama hatası',
            detail: error.message
        });
    }
});

// ============================================
// 5. TurkTelekom API
// ============================================
app.get('/api/turktelekom', async (req, res) => {
    try {
        const { sorgu, deger } = req.query;
        
        if (!sorgu || !deger) {
            return res.status(400).json({
                error: 'sorgu ve deger parametreleri gereklidir',
                example: '/api/turktelekom?sorgu=ad&deger=ali'
            });
        }

        const response = await fetchWithCF(
            `https://rinexturktelekomapi.gt.tc/api/turktelekom.php?sorgu=${sorgu}&deger=${encodeURIComponent(deger)}`,
            {
                headers: {
                    'Origin': 'https://rinexturktelekomapi.gt.tc',
                    'Referer': 'https://rinexturktelekomapi.gt.tc/'
                }
            }
        );

        try {
            const jsonData = JSON.parse(response.data);
            res.json({
                success: true,
                data: jsonData,
                source: 'rinexturktelekomapi.gt.tc'
            });
        } catch {
            res.set('Content-Type', 'text/plain');
            res.send(response.data);
        }

    } catch (error) {
        console.error('TurkTelekom API Hatası:', error.message);
        res.status(500).json({
            success: false,
            error: 'TurkTelekom sorgulama hatası',
            detail: error.message
        });
    }
});

// ============================================
// Ana Sayfa
// ============================================
app.get('/', (req, res) => {
    res.json({
        name: "Rinex API Gateway",
        version: "2.0.0",
        description: "Cloudflare korumalı API'ler için gateway",
        features: [
            "✅ Cloudflare korumasını aşar",
            "✅ JavaScript challenge çözer",
            "✅ Tüm API'leri tek noktadan sunar"
        ],
        endpoints: {
            iban: {
                path: "/api/iban",
                params: { iban: "TR280006256953335759003718" },
                example: "https://rinexsorguapilerimx.onrender.com/api/iban?iban=TR280006256953335759003718"
            },
            plaka: {
                path: "/api/plaka",
                params: { q: "34KG4978" },
                example: "https://rinexsorguapilerimx.onrender.com/api/plaka?q=34KG4978"
            },
            papara: {
                path: "/api/papara",
                params: { id: "1354693996" },
                example: "https://rinexsorguapilerimx.onrender.com/api/papara?id=1354693996"
            },
            secmen: {
                path: "/api/secmen",
                params: { action: "tc", tc: "18445070762" },
                example: "https://rinexsorguapilerimx.onrender.com/api/secmen?action=tc&tc=18445070762"
            },
            turktelekom: {
                path: "/api/turktelekom",
                params: { sorgu: "ad", deger: "ali" },
                example: "https://rinexsorguapilerimx.onrender.com/api/turktelekom?sorgu=ad&deger=ali"
            }
        },
        telegram: "@rinexdestek"
    });
});

// ============================================
// 404 Handler
// ============================================
app.use((req, res) => {
    res.status(404).json({
        error: 'Endpoint bulunamadı',
        available: ['/', '/api/iban', '/api/plaka', '/api/papara', '/api/secmen', '/api/turktelekom']
    });
});

// ============================================
// Sunucuyu Başlat
// ============================================
app.listen(PORT, () => {
    console.log(`🚀 Rinex API Gateway v2 çalışıyor: http://localhost:${PORT}`);
    console.log(`📡 Cloudflare korumasını aşan API hazır!`);
});
