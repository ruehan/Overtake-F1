#!/bin/bash

# Let's Encrypt SSL 인증서 설정 스크립트

echo "Let's Encrypt SSL 인증서 설정"
echo "=============================="
echo ""
echo "1. Homebrew로 certbot 설치:"
echo "   brew install certbot"
echo ""
echo "2. 인증서 발급 (nginx 중지 필요):"
echo "   sudo nginx -s stop"
echo "   sudo certbot certonly --standalone -d overtake-f1.com -d www.overtake-f1.com"
echo ""
echo "3. nginx 설정 업데이트:"
echo "   SSL 인증서 경로를 Let's Encrypt 경로로 변경"
echo "   - ssl_certificate /etc/letsencrypt/live/overtake-f1.com/fullchain.pem;"
echo "   - ssl_certificate_key /etc/letsencrypt/live/overtake-f1.com/privkey.pem;"
echo ""
echo "4. 자동 갱신 설정:"
echo "   sudo certbot renew --dry-run"
echo ""
echo "주의: 포트 80이 열려있어야 하며, DNS가 올바르게 설정되어 있어야 합니다."