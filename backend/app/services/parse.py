from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
from typing import Optional, Dict

META_NAME_MAP = {
    'og:title': 'title',
    'twitter:title': 'title',
    'og:description': 'description',
    'twitter:description': 'description',
    'description': 'description',
    'og:image': 'imageUrl',
    'twitter:image': 'imageUrl',
    'og:site_name': 'siteName',
}

PRIORITY_TITLE = ['og:title', 'twitter:title']
PRIORITY_DESC = ['og:description', 'twitter:description', 'description']
PRIORITY_IMAGE = ['og:image', 'twitter:image']
PRIORITY_SITENAME = ['og:site_name']

def _meta_content(tag) -> Optional[str]:
    if not tag:
        return None
    return tag.get('content') or tag.get('value')

def absolutize(base: str, url: Optional[str]) -> Optional[str]:
    if not url:
        return None
    return urljoin(base, url)

def process_html_content(base_url: str, html: str) -> str:
    """Process HTML to bypass paywalls and clean up content."""
    soup = BeautifulSoup(html, 'lxml')

    # Fix image sources
    for img in soup.find_all('img'):
        if 'data-gl-src' in img.attrs:
            img['src'] = urljoin(base_url, img['data-gl-src'])
            del img['data-gl-src']
        if 'data-gl-srcset' in img.attrs:
            img['srcset'] = urljoin(base_url, img['data-gl-srcset'])
            del img['data-gl-srcset']
        elif 'src' in img.attrs and not img['src'].startswith(('http', 'https')):
            img['src'] = urljoin(base_url, img['src'])
        if 'srcset' in img.attrs and not img['srcset'].startswith(('http', 'https')):
            img['srcset'] = urljoin(base_url, img['srcset'])

    # Handle figures
    for figure in soup.find_all('figure'):
        srcset_img = None
        for source in figure.find_all('source'):
            if 'srcset' in source.attrs:
                srcset_candidates = source['srcset'].split(',')
                if srcset_candidates:
                    srcset_img = srcset_candidates[0].strip().split()[0]
                break
        if srcset_img:
            img_tag = figure.find('img')
            if img_tag:
                img_tag['src'] = urljoin(base_url, srcset_img)
            else:
                new_img_tag = soup.new_tag('img', src=urljoin(base_url, srcset_img))
                figure.append(new_img_tag)

    # Remove script tags
    for script in soup.find_all('script'):
        script.extract()

    for aside in soup.find_all('aside'):
        aside.decompose()

    for anchor in soup.find_all('a', href=True):
        if anchor['href'].startswith('/picture-gallery'):
            anchor['href'] = urljoin(base_url, anchor['href'])

    return str(soup)

def extract_metadata(base_url: str, html: str) -> Dict[str, Optional[str]]:
    soup = BeautifulSoup(html, 'lxml')

    metas = {}
    for m in soup.find_all('meta'):
        key = m.get('property') or m.get('name')
        if not key:
            continue
        key = key.strip().lower()
        val = _meta_content(m)
        if val:
            metas.setdefault(key, val)

    def pick(keys):
        for k in keys:
            if k in metas and metas[k].strip():
                return metas[k].strip()
        return None

    title = pick(PRIORITY_TITLE) or (soup.title.string.strip() if soup.title and soup.title.string else None)
    description = pick(PRIORITY_DESC)
    image = pick(PRIORITY_IMAGE)
    site_name = pick(PRIORITY_SITENAME)

    if not site_name:
        try:
            site_name = urlparse(base_url).hostname
        except Exception:
            site_name = None

    image = absolutize(base_url, image)

    return {
        'title': title or None,
        'description': description or None,
        'imageUrl': image or None,
        'siteName': site_name or None,
    }