import requests
from bs4 import BeautifulSoup
import json
import csv
import time
from datetime import datetime
from urllib.parse import urljoin
import logging
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EastmoneyForumScraper:
    """东方财富论坛爬虫"""
    
    def __init__(self, keywords_file='keywords.json'):
        self.base_url = "https://guba.eastmoney.com"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        self.keywords = self.load_keywords(keywords_file)
        self.results = []
        
    def load_keywords(self, keywords_file):
        """加载关键词列表"""
        try:
            with open(keywords_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('keywords', [])
        except Exception as e:
            logger.error(f"加载关键词失败: {e}")
            return []
    
    def scrape_forum(self, max_posts=50):
        """爬取东方财富论坛"""
        logger.info(f"开始爬取东方财富论坛，最多爬取 {max_posts} 篇帖子")
        
        try:
            # 爬取热门讨论
            url = f"{self.base_url}/news"
            response = requests.get(url, headers=self.headers, timeout=10)
            response.encoding = 'utf-8'
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 查找帖子列表
            posts = soup.find_all('div', class_='news-item')[:max_posts]
            
            logger.info(f"找到 {len(posts)} 篇帖子")
            
            for idx, post in enumerate(posts):
                try:
                    # 提取帖子信息
                    title_elem = post.find('a', class_='title')
                    if not title_elem:
                        continue
                    
                    title = title_elem.get_text(strip=True)
                    link = title_elem.get('href', '')
                    
                    # 提取内容摘要
                    content_elem = post.find('div', class_='content')
                    content = content_elem.get_text(strip=True) if content_elem else ''
                    
                    # 提取时间
                    time_elem = post.find('span', class_='time')
                    post_time = time_elem.get_text(strip=True) if time_elem else ''
                    
                    # 匹配关键词
                    matched_keywords = self.match_keywords(title + ' ' + content)
                    
                    if matched_keywords:  # 只保存包含关键词的帖子
                        result = {
                            'title': title,
                            'content': content[:200] if content else '',  # 只保存前200字
                            'keywords': '; '.join(matched_keywords),
                            'keyword_count': len(matched_keywords),
                            'time': post_time,
                            'link': urljoin(self.base_url, link) if link else ''
                        }
                        self.results.append(result)
                        logger.info(f"[{idx+1}] 找到关键词: {title[:50]}...")
                    
                    # 礼貌延时
                    time.sleep(0.5)
                    
                except Exception as e:
                    logger.warning(f"处理帖子失败: {e}")
                    continue
            
            logger.info(f"爬取完成，找到 {len(self.results)} 篇包含关键词的帖子")
            
        except Exception as e:
            logger.error(f"爬取失败: {e}")
    
    def match_keywords(self, text):
        """匹配关键词"""
        matched = []
        for keyword in self.keywords:
            if keyword in text:
                matched.append(keyword)
        return matched
    
    def save_results(self, output_file='output/results.csv'):
        """保存结果到 CSV 文件"""
        try:
            os.makedirs(os.path.dirname(output_file), exist_ok=True)
            
            with open(output_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=[
                    'title', 'content', 'keywords', 'keyword_count', 'time', 'link'
                ])
                writer.writeheader()
                writer.writerows(self.results)
            
            logger.info(f"结果已保存到 {output_file}")
        except Exception as e:
            logger.error(f"保存结果失败: {e}")

def main():
    """主函数"""
    scraper = EastmoneyForumScraper()
    scraper.scrape_forum(max_posts=50)
    scraper.save_results()

if __name__ == '__main__':
    main()
