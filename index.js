// index.js - Rinex API Gateway (Render için)
const express = require('express');
const axios = require('axios');
const cors = require('cors');
const app = express();
const PORT = process.env.PORT || 3000;

// Middleware
app.use(cors());
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// Loglama
app.use((req, res, next) => {
    console.log(`[${new Date().toISOString()}] ${req.method} ${req.url}`);
    next();
});

// ============================================
// 1. IBAN API - /api/iban
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

        const response = await axios.get(
            `https://rinexibansorguapi.rf.gd/api.php?iban=${iban}`,
            {
                timeout: 30000,
                headers: {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                    'Accept': '*/*',
                    'Origin': 'https://rinexibansorguapi.rf.gd',
                    'Referer': 'https://rinexibansorguapi.rf.gd/'
                }
            }
        );

        // Ham yanıtı olduğu gibi gönder
        res.set('Content-Type', 'text/plain');
        res.send(response.data);

    } catch (error) {
        console.error('IBAN API Hatası:', error.message);
        res.status(500).send(`IBAN sorgulama hatası: ${error.message}`);
    }
});

// ============================================
// 2. Plaka API - /api/plaka
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

        const response = await axios.get(
            `https://rinexplakasorguapi.gt.tc/api/plaka.php?endpoint=ara&q=${encodeURIComponent(q)}`,
            {
                timeout: 30000,
                headers: {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                    'Accept': '*/*',
                    'Origin': 'https://rinexplakasorguapi.gt.tc',
                    'Referer': 'https://rinexplakasorguapi.gt.tc/'
                }
            }
        );

        res.set('Content-Type', 'text/plain');
        res.send(response.data);

    } catch (error) {
        console.error('Plaka API Hatası:', error.message);
        res.status(500).send(`Plaka sorgulama hatası: ${error.message}`);
    }
});

// ============================================
// 3. Papara API - /api/papara
// ============================================
app.get('/api/papara', async (req, res) => {
    try {
        const { id, name } = req.query;
        
        if (!id && !name) {
            return res.status(400).json({ 
                error: 'id veya name parametresi gereklidir',
                example: '/api/papara?id=1354693996 veya /api/papara?name=ÖZCAN'
            });
        }

        let url = 'http://rinexpaparasorguapi.rf.gd/api/papara.php';
        if (id) {
            url += `?id=${id}`;
        } else if (name) {
            url += `?name=${encodeURIComponent(name)}`;
        }

        const response = await axios.get(url, {
            timeout: 30000,
            headers: {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': '*/*',
                'Origin': 'http://rinexpaparasorguapi.rf.gd',
                'Referer': 'http://rinexpaparasorguapi.rf.gd/'
            }
        });

        res.set('Content-Type', 'text/plain');
        res.send(response.data);

    } catch (error) {
        console.error('Papara API Hatası:', error.message);
        res.status(500).send(`Papara sorgulama hatası: ${error.message}`);
    }
});

// ============================================
// 4. Seçmen API - /api/secmen
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

        const response = await axios.get(url, {
            timeout: 30000,
            headers: {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': '*/*',
                'Origin': 'https://rinexsecmensorguapu.gt.tc',
                'Referer': 'https://rinexsecmensorguapu.gt.tc/'
            }
        });

        res.set('Content-Type', 'text/plain');
        res.send(response.data);

    } catch (error) {
        console.error('Seçmen API Hatası:', error.message);
        res.status(500).send(`Seçmen sorgulama hatası: ${error.message}`);
    }
});

// ============================================
// 5. TurkTelekom API - /api/turktelekom
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

        const response = await axios.get(
            `https://rinexturktelekomapi.gt.tc/api/turktelekom.php?sorgu=${sorgu}&deger=${encodeURIComponent(deger)}`,
            {
                timeout: 30000,
                headers: {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                    'Accept': '*/*',
                    'Origin': 'https://rinexturktelekomapi.gt.tc',
                    'Referer': 'https://rinexturktelekomapi.gt.tc/'
                }
            }
        );

        res.set('Content-Type', 'text/plain');
        res.send(response.data);

    } catch (error) {
        console.error('TurkTelekom API Hatası:', error.message);
        res.status(500).send(`TurkTelekom sorgulama hatası: ${error.message}`);
    }
});

// ============================================
// Ana Sayfa - Tüm endpointleri listele
// ============================================
app.get('/', (req, res) => {
    res.json({
        name: "Rinex API Gateway",
        version: "1.0.0",
        description: "Tüm API'leri tek noktadan yönetin",
        endpoints: {
            iban: {
                path: "/api/iban",
                method: "GET",
                params: { iban: "TR280006256953335759003718" },
                example: "https://rinexsorguapilerim.onrender.com/api/iban?iban=TR280006256953335759003718"
            },
            plaka: {
                path: "/api/plaka",
                method: "GET",
                params: { q: "34KG4978" },
                example: "https://rinexsorguapilerim.onrender.com/api/plaka?q=34KG4978"
            },
            papara: {
                path: "/api/papara",
                method: "GET",
                params: { id: "1354693996", name: "ÖZCAN" },
                example: "https://rinexsorguapilerim.onrender.com/api/papara?id=1354693996"
            },
            secmen: {
                path: "/api/secmen",
                method: "GET",
                params: { action: "tc", tc: "18445070762" },
                example: "https://rinexsorguapilerim.onrender.com/api/secmen?action=tc&tc=18445070762"
            },
            turktelekom: {
                path: "/api/turktelekom",
                method: "GET",
                params: { sorgu: "ad", deger: "ali" },
                example: "https://rinexsorguapilerim.onrender.com/api/turktelekom?sorgu=ad&deger=ali"
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
    console.log(`🚀 Rinex API Gateway çalışıyor: http://localhost:${PORT}`);
    console.log(`📡 Ana sayfa: http://localhost:${PORT}`);
    console.log(`📋 Tüm API endpointleri hazır!`);
});
