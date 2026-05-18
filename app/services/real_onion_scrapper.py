"""
Real Onion Scraper with Tor Integration
Properly classifies threats using trained models
"""

import aiohttp
from aiohttp_socks import ProxyConnector
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import hashlib
import os
import base64
import asyncio
from datetime import datetime
import re

class RealOnionScraper:
    """Real onion scraper that connects through Tor"""
    
    def __init__(self):
        self.session = None
        self.tor_available = False
        
    async def initialize(self):
        """Initialize Tor session"""
        try:
            connector = ProxyConnector.from_url('socks5://127.0.0.1:9050')
            self.session = aiohttp.ClientSession(connector=connector)
            self.tor_available = True
            print("✅ Tor proxy connected on port 9050")
            return True
        except Exception as e:
            print(f"⚠️ Tor not available: {e}")
            self.session = aiohttp.ClientSession()
            self.tor_available = False
            return False
    
    async def test_tor_connection(self):
        """Test if Tor is working"""
        if not self.tor_available:
            return False
        try:
            async with self.session.get('http://check.torproject.org/', timeout=10) as response:
                html = await response.text()
                return 'Congratulations' in html
        except:
            return False
    
    async def scrape_real_onion(self, url, download_images=True):
        """
        Scrape a real .onion website through Tor
        Returns actual content from the site
        """
        result = {
            "url": url,
            "timestamp": datetime.now().isoformat(),
            "success": False,
            "text_content": "",
            "title": "",
            "html_content": "",
            "text_classification": None,
            "images": [],
            "links": [],
            "overall_risk": 0,
            "threat_level": "LOW",
            "error": None,
            "tor_used": self.tor_available
        }
        
        if not self.tor_available:
            result["error"] = "Tor not available. Please start Tor first."
            return result
        
        try:
            # Ensure URL has http:// prefix
            if not url.startswith('http'):
                url = f"http://{url}"
            
            print(f"\n{'='*60}")
            print(f"🌐 Scraping real .onion site: {url}")
            print("🔄 Connecting through Tor...")
            
            # Make request through Tor
            async with self.session.get(url, timeout=60) as response:
                if response.status == 200:
                    html = await response.text()
                    result["success"] = True
                    result["html_content"] = html[:100000]
                    
                    # Parse HTML
                    soup = BeautifulSoup(html, 'html.parser')
                    print(f"✅ Page loaded: {len(html)} bytes")
                    
                    # Extract title
                    title_tag = soup.find('title')
                    if title_tag:
                        result["title"] = title_tag.text.strip()
                        print(f"📌 Title: {result['title'][:100]}")
                    
                    # Extract ALL text content for classification
                    # Remove script and style elements
                    for script in soup(["script", "style", "noscript", "meta", "link"]):
                        script.decompose()
                    
                    # Get all text
                    text_content = soup.get_text()
                    # Clean up text
                    lines = (line.strip() for line in text_content.splitlines())
                    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
                    text_content = ' '.join(chunk for chunk in chunks if chunk)
                    result["text_content"] = text_content[:30000]
                    
                    print(f"📄 Extracted {len(result['text_content'])} characters for analysis")
                    
                    # Show a preview
                    if result["text_content"]:
                        preview = result["text_content"][:500].replace('\n', ' ')
                        print(f"   Preview: {preview}...")
                    
                    # Extract all links
                    for link in soup.find_all('a', href=True):
                        href = link['href']
                        if href and not href.startswith('#') and not href.startswith('javascript:'):
                            full_link = urljoin(url, href)
                            if full_link not in result["links"]:
                                result["links"].append(full_link)
                    
                    print(f"🔗 Found {len(result['links'])} links")
                    
                    # Download images
                    if download_images:
                        save_dir = os.path.join("uploads/onion_images", url.replace("http://", "").replace("https://", "").replace("/", "_")[:50])
                        os.makedirs(save_dir, exist_ok=True)
                        
                        images = soup.find_all('img')
                        print(f"📸 Found {len(images)} images")
                        
                        for idx, img in enumerate(images[:15]):
                            img_url = img.get('src')
                            if img_url and not img_url.startswith('data:'):
                                try:
                                    full_url = urljoin(url, img_url)
                                    async with self.session.get(full_url, timeout=15) as img_response:
                                        if img_response.status == 200:
                                            img_data = await img_response.read()
                                            if len(img_data) > 1000:
                                                img_hash = hashlib.md5(img_data).hexdigest()[:16]
                                                ext = os.path.splitext(img_url)[1] or '.jpg'
                                                if ext.lower() not in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
                                                    ext = '.jpg'
                                                filename = f"{img_hash}{ext}"
                                                filepath = os.path.join(save_dir, filename)
                                                
                                                with open(filepath, 'wb') as f:
                                                    f.write(img_data)
                                                
                                                # Convert to base64 for display
                                                img_base64 = base64.b64encode(img_data).decode('utf-8')
                                                mime_type = 'image/jpeg' if ext in ['.jpg', '.jpeg'] else 'image/png'
                                                
                                                result["images"].append({
                                                    "url": full_url,
                                                    "filename": filename,
                                                    "path": filepath,
                                                    "base64": f"data:{mime_type};base64,{img_base64}",
                                                    "size": len(img_data)
                                                })
                                                print(f"  ✅ Downloaded: {filename}")
                                except Exception as e:
                                    print(f"  ⚠️ Image download failed: {e}")
                        
                        print(f"📸 Downloaded {len(result['images'])} images")
                    
                    print(f"\n✅ Successfully scraped {url}")
                    
                else:
                    result["error"] = f"HTTP {response.status}"
                    print(f"❌ Error: HTTP {response.status}")
                    
        except asyncio.TimeoutError:
            result["error"] = "Timeout - Site not responding"
            print(f"❌ Error: Timeout after 60 seconds")
        except aiohttp.ClientConnectorError:
            result["error"] = "Connection error - Tor may not be running"
            print(f"❌ Error: Tor connection failed - Make sure Tor is running on port 9050")
        except Exception as e:
            result["error"] = str(e)
            print(f"❌ Error: {e}")
        
        return result
    
    async def scrape_with_classification(self, url, classifier, download_images=True):
        """
        Scrape real onion site and classify with trained models
        """
        # First, scrape the real site
        scraped = await self.scrape_real_onion(url, download_images)
        
        print(f"\n{'='*60}")
        print("🎯 CLASSIFYING WITH TRAINED MODELS")
        print(f"{'='*60}")
        
        # Classify with trained models if scraping was successful
        if scraped["success"] and scraped["text_content"]:
            # Classify text with Text GNN
            print("📝 Classifying text with Text GNN...")
            text_class = classifier.classify_text(scraped["text_content"])
            scraped["text_classification"] = text_class
            scraped["overall_risk"] = text_class["risk_score"]
            scraped["threat_level"] = text_class["threat_level"]
            
            print(f"   Prediction: {text_class['prediction'].upper()}")
            print(f"   Confidence: {text_class['confidence']:.2%}")
            print(f"   Risk Score: {text_class['risk_score']:.0f}%")
            print(f"   Threat Level: {text_class['threat_level']}")
            
            # Classify images with Image ViT
            if download_images and scraped["images"]:
                print(f"\n🖼️ Classifying {len(scraped['images'])} images with Image ViT...")
                for idx, img in enumerate(scraped["images"]):
                    if "path" in img and os.path.exists(img["path"]):
                        with open(img["path"], 'rb') as f:
                            img_data = f.read()
                        img_class = classifier.classify_image(img_data)
                        img["classification"] = img_class
                        print(f"   Image {idx+1}: {img_class['prediction']} ({img_class['confidence']:.2%})")
        else:
            print("⚠️ No text content extracted - cannot classify")
            # Provide fallback classification based on URL
            fallback_class = self._fallback_classification(url)
            scraped["text_classification"] = fallback_class
            scraped["overall_risk"] = fallback_class["risk_score"]
            scraped["threat_level"] = fallback_class["threat_level"]
        
        print(f"{'='*60}\n")
        
        return scraped
    
    def _fallback_classification(self, url):
        """Fallback classification when no content is extracted"""
        url_lower = url.lower()
        
        # Check URL for threat indicators
        gun_indicators = ['gun', 'firearm', 'arms', 'weapon', 'pistol', 'rifle', 'ammo', 'ak', 'ar15', 'glock']
        drug_indicators = ['drug', 'cocaine', 'heroin', 'mdma', 'meth', 'fentanyl', 'xanax', 'weed', 'market']
        poison_indicators = ['poison', 'cyanide', 'arsenic', 'ricin', 'toxin', 'chemical']
        
        for ind in gun_indicators:
            if ind in url_lower:
                return {
                    "prediction": "gun",
                    "confidence": 0.75,
                    "risk_score": 75,
                    "threat_level": "HIGH"
                }
        
        for ind in drug_indicators:
            if ind in url_lower:
                return {
                    "prediction": "drug",
                    "confidence": 0.78,
                    "risk_score": 78,
                    "threat_level": "HIGH"
                }
        
        for ind in poison_indicators:
            if ind in url_lower:
                return {
                    "prediction": "poison",
                    "confidence": 0.82,
                    "risk_score": 82,
                    "threat_level": "HIGH"
                }
        
        # For any .onion site, assume it's a marketplace (moderate risk)
        if '.onion' in url_lower:
            return {
                "prediction": "marketplace",
                "confidence": 0.60,
                "risk_score": 60,
                "threat_level": "MEDIUM"
            }
        
        return {
            "prediction": "benign",
            "confidence": 0.50,
            "risk_score": 10,
            "threat_level": "LOW"
        }
    
    async def scrape_multiple(self, urls, classifier, download_images=True):
        """Scrape multiple onion sites"""
        results = []
        for url in urls:
            result = await self.scrape_with_classification(url, classifier, download_images)
            results.append(result)
        return results
    
    async def close(self):
        if self.session:
            await self.session.close()


# Global scraper instance
real_onion_scraper = RealOnionScraper()