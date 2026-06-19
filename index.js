const express = require('express');
const puppeteer = require('puppeteer-extra');
const StealthPlugin = require('puppeteer-extra-plugin-stealth');
const cors = require('cors');
const app = express();
const PORT = process.env.PORT || 3000;

// Stealth plugin ile Cloudflare korumasını aş
puppeteer.use(StealthPlugin());

app.use(cors());
app.use(express.json());

// Browser instance (tekrar kullanım için)
let browser = null;

async function getBrowser() {
    if (!browser) {
        browser = await puppeteer.launch({
            headless: 'new',
            args: [
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage'
            ]
        });
    }
    return browser;
}

// ============================================
// Cloudflare korumalı siteyi aşan fonksiyon
// ============================================
async function fetchWithPuppeteer(url) {
    const browser = await getBrowser();
    const page = await browser.newPage();
    
    try {
        // Gerçek tarayıcı gibi davran
        await page.setUserAgent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36');
        await page.setExtraHTTPHeaders({
            'Accept-Language': 'tr-TR,tr;q=0.9,en;q=0.8'
        });
        
        // Sayfayı aç
        await page.goto(url, {
            waitUntil: 'networkidle2',
            timeout: 60000
        });
        
        // Cloudflare challenge'ı bekle (maksimum 30 saniye)
        await page.waitForFunction(
            () => {
                return !document.querySelector('body').innerHTML.includes('__test') &&
                       !document.querySelector('body').innerHTML.includes('aes.js');
            },
            { timeout: 30000 }
        );
        
        // Sayfa içeriğini al
        const content = await page.content();
        
        // JSON verisini bulmaya çalış
        const jsonMatch = content.match(/\{[\s\S]*\}/);
        if (jsonMatch) {
            return JSON.parse(jsonMatch[0]);
        }
        
        return { html: content };
        
    } catch (error) {
        console.error('Puppeteer hatası:', error.message);
        throw error;
    } finally {
        await page.close();
    }
}

// ============================================
// 1. IBAN API
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

        const url = `https://rinexibansorguapi.rf.gd/api.php?iban=${iban}`;
        const data = await fetchWithPuppeteer(url);
        
        res.json({
            success: true,
            data: data,
            source: 'rinexibansorguapi.rf.gd'
        });

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

        const url = `https://rinexplakasorguapi.gt.tc/api/plaka.php?endpoint=ara&q=${encodeURIComponent(q)}`;
        const data = await fetchWithPuppeteer(url);
        
        res.json({
            success: true,
            data: data,
            source: 'rinexplakasorguapi.gt.tc'
        });

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

        const data = await fetchWithPuppeteer(url);
        
        res.json({
            success: true,
            data: data,
            source: 'rinexpaparasorguapi.rf.gd'
        });

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

        const data = await fetchWithPuppeteer(url);
        
        res.json({
            success: true,
            data: data,
            source: 'rinexsecmensorguapu.gt.tc'
        });

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

        const url = `https://rinexturktelekomapi.gt.tc/api/turktelekom.php?sorgu=${sorgu}&deger=${encodeURIComponent(deger)}`;
        const data = await fetchWithPuppeteer(url);
        
        res.json({
            success: true,
            data: data,
            source: 'rinexturktelekomapi.gt.tc'
        });

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
        name: "Rinex API Gateway v3",
        version: "3.0.0",
        description: "Puppeteer ile Cloudflare korumasını aşan API Gateway",
        features: [
            "✅ Cloudflare JavaScript challenge çözer",
            "✅ Gerçek tarayıcı simülasyonu",
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
    console.log(`🚀 Rinex API Gateway v3 çalışıyor: http://localhost:${PORT}`);
    console.log(`🔐 Cloudflare korumasını Puppeteer ile aşıyor!`);
});
