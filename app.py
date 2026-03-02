"""
Klear K-Beauty Market Intelligence — Flask 서버
VS Code 터미널에서: python app.py
브라우저: http://localhost:5000
"""

from flask import Flask, jsonify, request, render_template
from datetime import datetime
import json, os, pathlib

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

app = Flask(__name__, static_folder="static", template_folder="templates")

# ─────────────────────────── 샘플 데이터 ───────────────────────────────────
def get_intelligence_data():
    return {
        "trend_count": 247, "trend_change": "+18.3%",
        "trends": [
            {"rank":1,"keyword":"Snail Mucin Routine",   "source":"Reddit",    "volume":"28k"},
            {"rank":2,"keyword":"Glass Skin Tutorial",   "source":"TikTok",    "volume":"19k"},
            {"rank":3,"keyword":"COSRX vs Klear compare","source":"Instagram", "volume":"7.4k"},
            {"rank":4,"keyword":"Ceramide Moisturizer",  "source":"Reddit",    "volume":"5.1k"},
            {"rank":5,"keyword":"Korean SPF Routine",    "source":"TikTok",    "volume":"4.8k"},
        ],
        "hot_keywords":    ["Snail Mucin","Glass Skin","Centella","Double Cleanse","K-Beauty Haul","COSRX","Skin Barrier"],
        "rising_keywords": ["Klear Serum","Bio-Wellness","Ceramide Cream","Peptide Ampoule","Fermented Essence","Hydrogel Patch"],
        "platform_stats":  {"TikTok":48,"Instagram":31,"Reddit":21},
        "sparkline_7d":    [30,45,38,55,72,60,88],
        "updated_at": datetime.now().strftime("%H:%M KST"),
    }

def get_outreach_data():
    return {
        "active_influencers":83, "mail_sent":67, "mail_total":100,
        "open_rate":44, "reply_rate":21,
        "influencers":[
            {"initials":"SR","name":"@skincarebyrose",  "followers":"234K","category":"Beauty",   "status":"open",   "status_label":"열람"},
            {"initials":"JL","name":"@jenloves_kbeauty","followers":"89K", "category":"Lifestyle","status":"replied","status_label":"회신 ✓"},
            {"initials":"MT","name":"@makeupwithmia",   "followers":"1.2M","category":"Makeup",   "status":"pending","status_label":"대기중"},
            {"initials":"CS","name":"@cleanskinsophia", "followers":"312K","category":"Skincare", "status":"sent",   "status_label":"발송됨"},
        ],
        "response_rate":31, "response_change":"-2.1%p",
        "updated_at": datetime.now().strftime("%H:%M KST"),
    }

def get_content_data():
    return {
        "content_count":136, "content_change":"+34.1%",
        "ab_test":{
            "variant_a":{"headline":"피부 장벽을 되살리는 클리어 루틴","ctr":3.2},
            "variant_b":{"headline":"3일 만에 달라진 결: Klear 후기",  "ctr":5.8,"winner":True},
        },
        "scenarios":[
            {"platform":"instagram","icon":"📸","title":"유리 피부 연출 GRWM — 15초 릴스",      "score":92},
            {"platform":"tiktok",   "icon":"▶", "title":"Before/After 세럼 챌린지 포맷",       "score":88},
            {"platform":"youtube",  "icon":"▷", "title":"K-Beauty 루틴 풀영상 (3분 쇼츠)",      "score":79},
            {"platform":"instagram","icon":"📸","title":"#KlearChallenge UGC 캠페인 시나리오",   "score":74},
        ],
        "updated_at": datetime.now().strftime("%H:%M KST"),
    }

# ─────────────────────────── 기본 API ──────────────────────────────────────
@app.route("/api/intelligence")
def api_intelligence(): return jsonify(get_intelligence_data())

@app.route("/api/outreach")
def api_outreach(): return jsonify(get_outreach_data())

@app.route("/api/content")
def api_content(): return jsonify(get_content_data())

@app.route("/api/all")
def api_all():
    return jsonify({"intelligence":get_intelligence_data(),"outreach":get_outreach_data(),"content":get_content_data()})


# ═══════════════════════════════════════════════════════════════════════════
# 카테고리별 SerpApi 검색 키워드 정의
# ─────────────────────────────────────────────────────────────────────────
# 4개 카테고리 모두 SerpApi → OpenAI 방식으로 통일
# ═══════════════════════════════════════════════════════════════════════════

CATEGORY_SEARCH_KEYWORDS = {
    "진입 장벽": "beauty cosmetics market entry barriers distribution competition local brands",
    "수출 규제": "cosmetics import regulation FDA requirements labeling banned ingredients certification",
    "문화":      "consumer culture beauty preference lifestyle local trend",
    "소비자 트렌드": "consumer trend demand skincare market growth popular 2026",
}

# ─── SerpApi 검색 (카테고리 통합) ──────────────────────────────────────────
def _fetch_serp_data_for_categories(
    country: str, item: str, categories: list, api_key: str
) -> tuple[str, list]:
    """
    선택된 모든 카테고리에 대해 SerpApi 구글 검색을 수행합니다.
    카테고리별로 최적화된 검색 쿼리를 사용해 관련도 높은 결과를 가져옵니다.
    Returns: (컨텍스트 텍스트 블록, raw_sources 리스트)
    """
    all_text    = ""
    all_sources = []

    if not api_key:
        all_text = "[데모] SERPAPI_KEY 미설정 — 실제 데이터를 가져오려면 .env에 SERPAPI_KEY를 입력하세요.\n"
        all_sources = [{"index": 1, "title": "SERPAPI_KEY 미설정", "snippet": "데모 모드", "link": "", "category": "전체"}]
        return all_text, all_sources

    import urllib.request, urllib.parse

    item_part = f" {item}" if item else ""

    for category in categories:
        keywords = CATEGORY_SEARCH_KEYWORDS.get(category, "beauty cosmetics")
        query    = f"{country}{item_part} {keywords} 2026"

        try:
            params = urllib.parse.urlencode({
                "q":       query,
                "api_key": api_key,
                "num":     5,
                "hl":      "en",
                "gl":      "us",
            })
            with urllib.request.urlopen(
                f"https://serpapi.com/search.json?{params}", timeout=10
            ) as resp:
                results = json.loads(resp.read().decode()).get("organic_results", [])[:5]

            if results:
                all_text += f"\n── [{category}] 검색 결과 (쿼리: {query}) ──\n"
                for i, r in enumerate(results):
                    all_sources.append({
                        "index":    len(all_sources) + 1,
                        "title":    r.get("title", ""),
                        "snippet":  r.get("snippet", ""),
                        "link":     r.get("link", ""),
                        "category": category,
                    })
                    all_text += f"[{category}-{i+1}] {r.get('title','')}\n{r.get('snippet','')}\n\n"
            else:
                all_text += f"[{category}] 검색 결과 없음\n\n"

        except Exception as e:
            all_text    += f"[{category}] SerpApi 오류: {e}\n\n"
            all_sources.append({
                "index":    len(all_sources) + 1,
                "title":    f"SerpApi 오류 ({category})",
                "snippet":  str(e),
                "link":     "",
                "category": category,
            })

    return all_text, all_sources


# ─── 카테고리별 AI 분석 지침 ────────────────────────────────────────────────
_CATEGORY_PROMPT = {
    "진입 장벽": (
        "## 🚧 시장 진입 장벽\n"
        "- 유통 채널 구조, 현지 경쟁 브랜드, 가격 민감도, 브랜드 신뢰도 장벽을 분석하세요.\n"
        "- 검색 데이터에 근거해 구체적인 장벽 요소를 서술하세요."
    ),
    "수출 규제": (
        "## 📋 수출 규제 및 법적 요건\n"
        "- 화장품 수입 규정, 인증 요구사항(예: FDA 등록), 금지 성분, 라벨링 규정을 분석하세요.\n"
        "- 검색 데이터에 근거한 내용만 서술하고, 불확실한 규정은 '추가 확인 필요'로 표기하세요."
    ),
    "문화": (
        "## 🌏 문화적 특성\n"
        "- 현지 뷰티 문화, 피부 관리 습관, 미적 기준, K-뷰티 인식을 분석하세요.\n"
        "- 문화적 선호도와 금기 사항도 포함하세요."
    ),
    "소비자 트렌드": (
        "## 📈 소비자 트렌드 및 전략적 시사점\n"
        "- 소비 패턴, 인기 성분/제품, SNS 트렌드, 구매 채널 선호도를 분석하세요.\n"
        "- Klear 브랜드가 이 트렌드를 활용할 수 있는 실질적 전략도 제시하세요."
    ),
}


# ─── 실시간 트렌드 키워드 분석 (/api/trend-keywords) ───────────────────────
@app.route("/api/trend-keywords", methods=["POST"])
def api_trend_keywords():
    try:
        data     = request.get_json(force=True)
        platform = data.get("platform", "전체").strip()
        category = data.get("category", "K-뷰티 스킨케어").strip()

        SERP_API_KEY   = os.environ.get("SERPAPI_KEY", "")
        OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")

        # 1. SerpApi 검색
        search_query        = f"K-beauty {category} trend {platform} 2026 popular keywords"
        raw_sources         = []
        search_results_text = ""

        if SERP_API_KEY:
            try:
                import urllib.request, urllib.parse
                params = urllib.parse.urlencode({
                    "q": search_query, "api_key": SERP_API_KEY,
                    "num": 5, "hl": "en", "gl": "us"
                })
                with urllib.request.urlopen(
                    f"https://serpapi.com/search.json?{params}", timeout=10
                ) as resp:
                    serp_data = json.loads(resp.read().decode())
                for i, r in enumerate(serp_data.get("organic_results", [])[:5]):
                    raw_sources.append({
                        "index": i+1, "title": r.get("title",""),
                        "snippet": r.get("snippet",""), "link": r.get("link","")
                    })
                    search_results_text += f"[{i+1}] {r.get('title','')}\n{r.get('snippet','')}\n\n"
            except Exception as e:
                search_results_text = f"(SerpApi 오류: {e})\n"
                raw_sources = [{"index":1,"title":"검색 오류","snippet":str(e),"link":""}]
        else:
            search_results_text = f"[데모] SERP_API_KEY 미설정. 쿼리: {search_query}\n"
            raw_sources = [{"index":1,"title":"SERP_API_KEY 미설정","snippet":"데모 모드","link":""}]

        # 2. System/User Prompt
        system_prompt = (
            "당신은 K-뷰티 소셜미디어 트렌드 전문 애널리스트입니다. "
            "제공된 실시간 검색 데이터만 근거로 분석하세요. "
            "데이터에 없는 내용은 반드시 '정보 없음'으로 표기하고 절대 지어내지 마세요. "
            "답변은 마크다운으로 작성하세요."
        )
        user_prompt = (
            f"**분석 플랫폼:** {platform}\n**분석 카테고리:** {category}\n\n"
            f"**실시간 검색 데이터 (쿼리: {search_query}):**\n\n{search_results_text}\n\n"
            "위 데이터를 바탕으로 아래 항목을 분석해주세요:\n\n"
            "## 🔥 현재 주목 트렌드\n- 가장 주목받는 키워드와 이유를 분석하세요.\n\n"
            "## 📈 급상승 키워드\n- 최근 급격히 언급량이 증가하는 키워드를 나열하세요.\n\n"
            "## 💡 브랜드 전략 시사점\n- K-뷰티 브랜드가 이 트렌드를 활용할 수 있는 실질적 전략을 제시하세요.\n"
        )

        # 3. OpenAI 분석
        analysis_text = ""
        if OPENAI_API_KEY:
            try:
                from openai import OpenAI
                client = OpenAI(api_key=OPENAI_API_KEY)
                res = client.chat.completions.create(
                    model="gpt-4-turbo-preview",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user",   "content": user_prompt}
                    ],
                    temperature=0.3, max_tokens=1200,
                )
                analysis_text = res.choices[0].message.content
            except Exception as e:
                analysis_text = f"> ⚠️ OpenAI 오류: {e}\n\n.env에 OPENAI_API_KEY를 설정하세요."
        else:
            analysis_text = (
                f"## ⚠️ 데모 모드 (OPENAI_API_KEY 미설정)\n\n"
                f"**플랫폼:** {platform} · **카테고리:** {category}\n\n"
                "### 🔥 현재 주목 트렌드\n- OPENAI_API_KEY 설정 후 실제 분석이 실행됩니다.\n\n"
                "### 📈 급상승 키워드\n- SERP_API_KEY 설정 시 실시간 데이터 수집됩니다.\n\n"
                "### 💡 브랜드 전략 시사점\n- 정보 없음 (데모 모드)\n"
            )

        return jsonify({
            "success":        True,
            "analysis":       analysis_text,
            "system_prompt":  system_prompt,
            "search_results": raw_sources,
            "analyzed_at":    datetime.now().strftime("%Y-%m-%d %H:%M KST"),
        })

    except Exception as e:
        return jsonify({"error": f"서버 오류: {e}"}), 500


# ─── 국가별 진입 전략 분석 (/api/market-entry) ─────────────────────────────
@app.route("/api/market-entry", methods=["POST"])
def api_market_entry():
    """
    4개 카테고리(진입 장벽, 수출 규제, 문화, 소비자 트렌드) 모두
    SerpApi 실시간 검색 → OpenAI GPT-4 분석으로 통일된 파이프라인.
    """
    try:
        body = request.get_json(force=True)
        target_country      = body.get("target_country", "").strip()
        target_item         = "K-beauty skincare cosmetics"
        selected_categories = body.get("selected_categories",
                                       ["진입 장벽", "수출 규제", "문화", "소비자 트렌드"])

        if not target_country:
            return jsonify({"error": "진출 국가를 입력하세요."}), 400
        if not selected_categories:
            return jsonify({"error": "분석 항목을 하나 이상 선택하세요."}), 400

        # API 키 로드
        SERPAPI_KEY    = os.environ.get("SERPAPI_KEY", "")
        OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")

        # ── SerpApi: 선택된 모든 카테고리 검색 ──────────────────────────────
        search_text, search_sources = _fetch_serp_data_for_categories(
            target_country, target_item, selected_categories, SERPAPI_KEY
        )

        # ── Prompt 구성 ──────────────────────────────────────────────────────
        categories_str    = ", ".join(selected_categories)
        excluded          = ", ".join(c for c in _CATEGORY_PROMPT if c not in selected_categories) or "없음"
        analysis_sections = "\n\n".join(
            _CATEGORY_PROMPT[c] for c in selected_categories if c in _CATEGORY_PROMPT
        )

        system_prompt = (
            "당신은 10년 경력의 글로벌 뷰티 전략 컨설턴트입니다.\n"
            f"[분석 요청 항목]: {categories_str}\n"
            f"[분석 제외 항목]: {excluded} — 이 항목은 절대 언급하지 마세요.\n\n"
            "데이터 처리 원칙:\n"
            "  - 아래 제공된 실시간 검색 데이터만을 근거로 분석하세요.\n"
            "  - 🚨 부정적 표현 금지: 검색 데이터에 직접적인 내용이 부족하더라도 '정보 없음', '유감스럽게도', '분석 불가' 같은 표현은 절대 쓰지 마세요.\n"
            "  - 전문가적 추론 및 검토 권장: 직접적인 정보가 없다면 시장 성장률 등 주변 데이터로 유추하여 작성하되, 해당 문장 끝에 '이 부분은 실무적인 추가 확인이 권장됩니다'라고 덧붙이세요.\n"
            "  - 🚨 할루시네이션(없는 사실 지어내기) 금지: 데이터에 없는 내용을 절대 무에서 유로 창조하지 마세요.\n"
            "  - 답변은 마크다운 형식(## 헤딩, - 리스트, **볼드**)으로 작성하세요.\n"
            "  - 검색 데이터를 근거로 서술할 때는 반드시 해당 출처 번호를 [1], [2] 형태로 문장 끝에 표기하세요.\n"
            "  - 각주 번호는 아래 검색 데이터의 [SOURCE 번호]와 일치해야 합니다."
        )

        # 번호 붙인 출처 목록 생성
        numbered_sources = ""
        for i, s in enumerate(search_sources, 1):
            numbered_sources += f"[SOURCE {i}] ({s.get('category','')}) {s.get('title','')}\n{s.get('snippet','')}\n\n"

        item_line   = f"**분석 품목:** {target_item}\n" if target_item else ""
        user_prompt = (
            f"**분석 대상국:** {target_country}\n"
            f"{item_line}"
            f"**분석 요청 항목:** {categories_str}\n\n"
            f"**실시간 검색 데이터 (SerpApi Google Search):**\n"
            f"{numbered_sources}\n"
            f"위 데이터를 근거로 선택된 항목만 분석하세요. 근거 문장마다 [SOURCE 번호]를 [1], [2] 형태로 반드시 표기하세요:\n\n"
            f"{analysis_sections}\n"
        )

        # ── OpenAI GPT-4 분석 ────────────────────────────────────────────────
        if OPENAI_API_KEY:
            try:
                from openai import OpenAI
                client = OpenAI(api_key=OPENAI_API_KEY)
                res = client.chat.completions.create(
                    model="gpt-4-turbo-preview",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user",   "content": user_prompt},
                    ],
                    temperature=0.3,
                    max_tokens=2500,
                )
                analysis_text = res.choices[0].message.content
            except Exception as e:
                analysis_text = f"> ⚠️ OpenAI 오류: {e}\n\n.env에 OPENAI_API_KEY를 설정하세요."
        else:
            analysis_text = (
                f"## ⚠️ 데모 모드 (OPENAI_API_KEY 미설정)\n\n"
                f"**분석 대상:** {target_country}"
                + (f" × {target_item}" if target_item else "") + "\n"
                f"**선택 항목:** {categories_str}\n\n"
                + "\n\n".join(
                    f"### {c}\n- .env에 OPENAI_API_KEY를 설정하면 실제 분석이 실행됩니다."
                    for c in selected_categories
                )
            )

        # ── 응답 반환 ────────────────────────────────────────────────────────
        return jsonify({
            "success":        True,
            "analysis":       analysis_text,
            "system_prompt":  system_prompt,
            "search_results": search_sources,
            "analyzed_at":    datetime.now().strftime("%Y-%m-%d %H:%M KST"),
            "debug": {
                "search_sources":   search_sources,
                "search_text":      search_text,
                "system_prompt":    system_prompt,
                "selected_categories": selected_categories,
                "timestamp":        datetime.now().strftime("%Y-%m-%d %H:%M:%S KST"),
            }
        })

    except Exception as e:
        return jsonify({"error": f"서버 오류: {e}"}), 500

# ─── 콘텐츠 생성 엔진 (Instagram / 숏폼 등) ────────────────────────────────
@app.route("/api/generate-content", methods=["POST"])
def api_generate_content():
    import os
    from flask import jsonify, request
    try:
        data = request.get_json(force=True)
        content_type = data.get("type", "instagram")
        product_name = data.get("product_name", "").strip()
        target_audience = data.get("target_audience", "").strip()
        key_point = data.get("key_point", "").strip()
        
        # 🚀 클라이언트(화면)에서 보낸 프롬프트를 우선적으로 사용!
        custom_prompt = data.get("system_prompt", "").strip()

        OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
        if not OPENAI_API_KEY:
            return jsonify({"success": False, "error": ".env 파일에 OPENAI_API_KEY가 없습니다."})

        # 1. AI 프롬프트 세팅 (화면에서 보낸 값이 있으면 그걸 쓰고, 없으면 기본값 사용)
        if custom_prompt:
            system_prompt = custom_prompt
        else:
            system_prompt = "당신은 트렌디하고 감각적인 K-뷰티 전문 SNS 콘텐츠 마케터입니다. (이하 생략)"

        user_prompt = f"📦 제품명: {product_name}\n"
        if target_audience: user_prompt += f"🎯 타겟 고객: {target_audience}\n"
        if key_point: user_prompt += f"✨ 소구 포인트: {key_point}\n"

        # 2. OpenAI 호출
        from openai import OpenAI
        client = OpenAI(api_key=OPENAI_API_KEY)
        res = client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
            max_tokens=1000
        )

        result_text = res.choices[0].message.content

        # 3. 결과 반환
        return jsonify({"success": True, "result": result_text})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)})
    

# ─────────────────────── Reddit 트렌드 분석 (Apify + OpenAI) ──────────────
@app.route('/api/trend/reddit', methods=['POST'])
def api_trend_reddit():
    """
    Apify로 r/AsianBeauty + r/SkincareAddiction 동시 수집 (총 100개)
    두 커뮤니티 통합 데이터에서 공통/중복 언급 키워드 TOP5 추출 (언급량 내림차순)
    """
    try:
        APIFY_TOKEN    = os.environ.get('APIFY_API_TOKEN', '')
        OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', '')

        if not APIFY_TOKEN:
            return jsonify({'error': '.env에 APIFY_API_TOKEN이 설정되어 있지 않습니다.'}), 400
        if not OPENAI_API_KEY:
            return jsonify({'error': '.env에 OPENAI_API_KEY가 설정되어 있지 않습니다.'}), 400

        # ── 1. Apify로 두 서브레딧 동시 수집 ──────────────────────────────
        from apify_client import ApifyClient
        client = ApifyClient(APIFY_TOKEN)

        run_input = {
            'startUrls': [
                {'url': 'https://www.reddit.com/r/AsianBeauty/new/'},
                {'url': 'https://www.reddit.com/r/SkincareAddiction/new/'},
            ],
            'maxItems': 30,
            'proxyConfiguration': {'useApifyProxy': True},
        }

        run   = client.actor('trudax/reddit-scraper-lite').call(run_input=run_input)
        items = list(client.dataset(run['defaultDatasetId']).iterate_items())

        if not items:
            return jsonify({'error': 'Apify에서 데이터를 가져오지 못했습니다.'}), 500

        # ── 2. 텍스트 합치기 (출처 서브레딧 표기) ──────────────────────────
        combined_text = ''
        for item in items:
            title      = item.get('title') or item.get('title_text') or ''
            body       = item.get('text')  or item.get('selftext') or item.get('body') or ''
            source_url = item.get('url', '')
            if 'AsianBeauty' in source_url:
                source = 'r/AsianBeauty'
            elif 'SkincareAddiction' in source_url:
                source = 'r/SkincareAddiction'
            else:
                source = 'r/Reddit'
            if title or body:
                combined_text += f'[{source}] 제목: {title}\n본문: {body}\n\n'

        # ── 3. OpenAI gpt-4o-mini 분석 ─────────────────────────────────────
        from openai import OpenAI
        ai_client = OpenAI(api_key=OPENAI_API_KEY)

        prompt = (
            "너는 미국 현지 스킨케어 시장을 분석하는 수석 데이터 애널리스트야.\n"
            "레딧(Reddit)의 'r/AsianBeauty'와 'r/SkincareAddiction'에서 수집된 미국 유저들의 스킨케어/선케어 게시글 데이터야.\n\n"
            "[게시글 데이터]\n"
            + combined_text +
            "\n[수행 작업 및 분석 가이드라인]\n"
            "우리는 미국 시장에 '백탁 없는 K-뷰티 선세럼(Sun Serum)'을 런칭할 계획이야. **미국 소비자들의 핵심 스킨케어/선케어 트렌드 키워드 TOP 10**을 도출해.\n\n"
            "1. 절대적 객관성 유지 (할루시네이션 금지): 오직 '제공된 텍스트' 내에서만 추출할 것.\n\n"
            "2. 페인포인트 발굴: White cast(백탁), Pilling(화장 밀림), Greasy(기름짐) 등 기존 선크림에 대한 불만을 우선적으로 찾아낼 것.\n\n"
            "3. 니즈 발굴: Lightweight, Hydrating, Glass skin 등 가벼운 제형과 광채 피부에 대한 열망을 찾아낼 것.\n\n"
            "4. 키워드 그룹핑: SPF/Sunscreen/Sunblock 등 유사어는 대표 하나로 통합할 것.\n\n"
            "5. 🚨 배제 대상: 물류(Shipping, Customs), 쇼핑몰 관련, 메이크업(색조) 관련 단어는 무조건 제외할 것.\n\n"
            "6. 🚨 뻔한 단어 배제: 'Sunscreen', 'SPF', 'Sunblock' 등 자외선 차단제 단어 자체는 키워드 선정에서 아예 제외하고, 그로 인한 구체적인 피부 변화(효과/불만)나 특정 성분명에만 집중할 것.\n\n"
            "[출력 형식]\n"
            "- 마크다운 기호 없이 오직 순수한 JSON 배열만 출력할 것.\n"
            "- 반드시 mentions 값 기준 내림차순으로 정렬해서 출력할 것.\n"
            "- 🚨 모든 'keyword'는 반드시 소문자(lowercase)로 통일해서 출력할 것.\n"
            "- 'summary'는 이 키워드가 선세럼 마케팅에 왜 중요한지 **존댓말(합쇼체)**로 한국어 2~3줄 분석.\n\n"
            '[\n'
            '  {{\n'
            '    "keyword": "white cast",\n'
            '    "mentions": 3,\n'
            '    "summary": "한국어 요약 분석 (반드시 존댓말/합쇼체로 작성)"\n'
            '  }}\n'
            ']'
        )

        res = ai_client.chat.completions.create(
            model='gpt-4o-mini',
            messages=[{'role': 'user', 'content': prompt}],
            temperature=0.3,
            max_tokens=1000,
        )

        raw      = res.choices[0].message.content.strip()
        raw      = raw.replace('```json', '').replace('```', '').strip()
        keywords = json.loads(raw)

        # mentions 내림차순 정렬 (백엔드에서 확실히 보장)
        keywords = sorted(keywords, key=lambda x: x.get('mentions', 0), reverse=True)

        return jsonify({
            'success':    True,
            'keywords':   keywords,
            'post_count': len(items),
            'analyzed_at': datetime.now().strftime('%Y-%m-%d %H:%M KST'),
        })

    except Exception as e:
        return jsonify({'error': f'분석 오류: {str(e)}'}), 500




# ─────────────────────── YouTube 트렌드 분석 (Apify + OpenAI) ─────────────
@app.route('/api/trend/youtube', methods=['POST'])
def api_trend_youtube():
    """
    Apify youtube-scraper로 K-뷰티 관련 유튜브 영상 수집 (미국 타겟, 총 30개)
    제목+설명 통합 분석 → gpt-4o-mini로 트렌드 키워드 TOP10 추출 (언급량 내림차순)
    """
    try:
        APIFY_TOKEN    = os.environ.get('APIFY_API_TOKEN', '')
        OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', '')

        if not APIFY_TOKEN:
            return jsonify({'error': '.env에 APIFY_API_TOKEN이 설정되어 있지 않습니다.'}), 400
        if not OPENAI_API_KEY:
            return jsonify({'error': '.env에 OPENAI_API_KEY가 설정되어 있지 않습니다.'}), 400

        # ── 1. Apify로 유튜브 영상 수집 ──────────────────────────────────
        from apify_client import ApifyClient
        client = ApifyClient(APIFY_TOKEN)

        keyword_list = [
            "Best skincare routine 2026",
            "Morning skincare for glowing skin",
            "Skincare steps for healthy skin",
        ]

        all_items = []
        for keyword in keyword_list:
            try:
                run_input = {
                    'searchQueries': [keyword],
                    'maxResults': 3,
                    'proxyConfiguration': {
                        'useApifyProxy': True,
                        'apifyProxyCountry': 'US',
                    },
                }
                run   = client.actor('streamers/youtube-scraper').call(run_input=run_input)
                items = list(client.dataset(run['defaultDatasetId']).iterate_items())
                all_items.extend(items)
            except Exception as e:
                print(f"[YouTube] '{keyword}' 수집 오류: {e}")
                continue

        if not all_items:
            return jsonify({'error': 'Apify에서 유튜브 데이터를 가져오지 못했습니다.'}), 500

        # ── 2. 제목 + 설명 합치기 ─────────────────────────────────────────
        combined_text = ''
        for item in all_items:
            title       = item.get('title') or item.get('name') or ''
            description = item.get('description') or item.get('text') or ''
            if title or description:
                combined_text += f'제목: {title}\n설명: {description}\n\n'

        # ── 3. OpenAI gpt-4o-mini 분석 ───────────────────────────────────
        from openai import OpenAI
        ai_client = OpenAI(api_key=OPENAI_API_KEY)

        prompt = (
            "너는 미국 현지 스킨케어 트렌드를 분석하는 수석 애널리스트야.\n"
            "미국 뷰티 유튜브 영상들의 제목과 더보기란 데이터야.\n\n"
            "[게시글 데이터]\n"
            + combined_text +
            "\n[수행 작업 및 분석 가이드라인]\n"
            "우리는 미국 시장에 '가볍고 백탁 없는 선세럼'을 런칭할 계획이야. **미국 소비자들의 핵심 스킨케어/선케어 트렌드 키워드 TOP 10**을 도출해.\n\n"
            "1. 절대적 객관성 유지 (할루시네이션 금지): 오직 '제공된 텍스트' 내에서만 추출할 것.\n\n"
            "2. 기존 선크림의 한계(백탁, 밀림)와 원하는 피부 표현(Glass skin, 윤광)에 관련된 구체적인 키워드를 추출할 것.\n\n"
            "3. 키워드 그룹핑: SPF/Sunscreen/Sunblock 등 유사어는 대표 하나로 통합할 것.\n\n"
            "4. 🚨 배제 대상: Link, Subscribe, Amazon, Discount code 등 홍보 관련 키워드와 Makeup 등 색조 관련 키워드는 무조건 제외할 것.\n\n"
            "5. 🚨 뻔한 단어 배제: 'Sunscreen', 'SPF', 'Sunblock' 등 자외선 차단제 단어 자체는 키워드 선정에서 아예 제외하고, 그로 인한 구체적인 피부 변화(효과/불만)나 특정 성분명에만 집중할 것.\n\n"
            "[출력 형식]\n"
            "- 마크다운 기호 없이 오직 순수한 JSON 배열만 출력할 것.\n"
            "- 반드시 mentions 값 기준 내림차순으로 정렬해서 출력할 것.\n"
            "- 🚨 모든 'keyword'는 반드시 소문자(lowercase)로 통일해서 출력할 것.\n"
            "- 'summary'는 이 키워드가 선세럼 마케팅에 왜 중요한지 **존댓말(합쇼체)**로 한국어 2~3줄 분석.\n\n"
            "[\n"
            "  {{\n"
            "    \"keyword\": \"lightweight texture\",\n"
            "    \"mentions\": 3,\n"
            "    \"summary\": \"한국어 요약 (반드시 존댓말/합쇼체로 작성)\"\n"
            "  }}\n"
            "]"
        )

        res = ai_client.chat.completions.create(
            model='gpt-4o-mini',
            messages=[{'role': 'user', 'content': prompt}],
            temperature=0.3,
            max_tokens=1500,
        )

        raw      = res.choices[0].message.content.strip()
        raw      = raw.replace('```json', '').replace('```', '').strip()
        keywords = json.loads(raw)

        # mentions 내림차순 정렬 (백엔드에서 확실히 보장)
        keywords = sorted(keywords, key=lambda x: x.get('mentions', 0), reverse=True)

        return jsonify({
            'success':    True,
            'keywords':   keywords,
            'video_count': len(all_items),
            'analyzed_at': datetime.now().strftime('%Y-%m-%d %H:%M KST'),
        })

    except Exception as e:
        return jsonify({'error': f'분석 오류: {str(e)}'}), 500



# ═══════════════════════════════════════════════════════════════════════════
# TikTok/Instagram 분석용 설정 (APIFY_API_TOKEN 사용)
# ═══════════════════════════════════════════════════════════════════════════

EXCLUDED_TAGS = [
    # Apify 검색 미끼 태그 (수집용으로만 쓰고 결과엔 노출 안 함)
    'sephorahaul', 'targetbeauty', 'ultabeauty',
    'skincareroutine', 'skincaretips', 'glowingskin', 'healthyskin',
    'sunscreen', 'spf',  # 수집 시드 — 결과엔 뻔해서 제외
    # 범용 뷰티 태그 (너무 넓어서 마케팅 가치 없음)
    'beauty', 'skincare', 'makeup', 'cosmetics',
    # TikTok 알고리즘 태그 (트렌드와 무관)
    'fyp', 'foryou', 'foryoupage', 'viral', 'trending',
]

PLATFORM_PROMPTS = {
    'TikTok': """너는 미국 Z세대를 타겟으로 한 스킨케어 및 뷰티 트렌드 애널리스트야.
다음은 미국 TikTok 뷰티 영상에서 실시간으로 수집된 해시태그 빈도 데이터와 영상 캡션이야.

[해시태그 빈도 데이터]
{tags_str}

[영상 캡션 샘플]
{sample_txt}

[수행 작업 및 분석 가이드라인]
우리의 핵심 목표는 미국 시장에 '백탁 없고 촉촉한 K-뷰티 선세럼(Sun Serum)'을 런칭하는 거야.
데이터를 심층 분석하여 현재 Z세대가 열광하는 **스킨케어/선케어 핵심 트렌드 키워드 TOP {limit}**을 도출해.

1. 타겟팅 최우선 순위 (Pain points & Desires):
   - 기존 자외선 차단제의 불만: White cast(백탁), Pilling(밀림), Sticky(끈적임), Heavy(무거움)
   - 선호하는 피부 표현 및 제형: Glass skin(유리알 광채), Glowing, Hydrating, Lightweight

2. 🚨 배제 대상 (Negative Filter) 필수 적용:
   - Makeup, Fenty, Lip, Eyeshadow 등 색조 화장품 키워드 무조건 제외.
   - Shipping, Haul, Sephora, Target 등 유통/구매 관련 단어 배제.
   - Skin, Face, Beauty 같은 뻔한 범용 단어 배제.
   - 🚨 뻔한 단어 배제: 'Sunscreen', 'SPF', 'Sunblock' 등 자외선 차단제 단어 자체는 키워드 선정에서 아예 제외하고, 그로 인한 구체적인 피부 변화(효과/불만)나 특정 성분명에만 집중할 것.

[출력 형식]
- 마크다운 없이 순수 JSON 배열만 출력.
- 🚨 모든 'keyword'는 반드시 소문자(lowercase)로 통일해서 출력할 것.
- 'summary'는 이 키워드가 선세럼 마케팅에 왜 중요한지 **존댓말(합쇼체)**로 한국어 2~3줄 분석.

[
  {{
    "keyword": "white cast",
    "mentions": 카운트숫자,
    "summary": "한국어 요약 분석 (반드시 존댓말/합쇼체로 작성)"
  }}
]""",

    'Instagram': """너는 미국 밀레니얼/Z세대를 타겟으로 한 스킨케어 트렌드 애널리스트야.
다음은 미국 Instagram 게시물에서 수집된 해시태그 데이터와 캡션이야.

[해시태그 빈도 데이터]
{tags_str}

[게시물 캡션 샘플]
{sample_txt}

[수행 작업 및 분석 가이드라인]
우리의 핵심 목표는 미국 시장에 '백탁 없고 광채를 주는 선세럼(Sun Serum)'을 런칭하는 거야.
데이터를 심층 분석하여 현재 유저들이 주목하는 **스킨케어/선케어 트렌드 키워드 TOP {limit}**을 도출해.

1. 타겟팅 최우선 순위:
   - 기존 선크림의 한계(백탁, 화장 밀림 등)와 이를 대체할 가벼운 제형(Lightweight, Serum-like).
   - 인스타그래머블한 피부 표현: Glass skin, Dewy finish, Glowing skin.

2. 🚨 배제 대상 (Negative Filter) 필수 적용:
   - Makeup, Color cosmetics 등 색조 화장품 관련 키워드 철저히 제외.
   - PR package, Discount code, Link in bio 등 홍보성 단어 배제.
   - Skin, Face, Beauty 같은 뻔한 범용 단어 배제.
   - 🚨 뻔한 단어 배제: 'Sunscreen', 'SPF', 'Sunblock' 등 자외선 차단제 단어 자체는 키워드 선정에서 아예 제외하고, 그로 인한 구체적인 피부 변화(효과/불만)나 특정 성분명에만 집중할 것.

[출력 형식]
- 마크다운 없이 순수 JSON 배열만 출력.
- 🚨 모든 'keyword'는 반드시 소문자(lowercase)로 통일해서 출력할 것.
- 'summary'는 이 키워드가 선세럼 마케팅에 왜 중요한지 **존댓말(합쇼체)**로 한국어 2~3줄 분석.

[
  {{
    "keyword": "glass skin",
    "mentions": 카운트숫자,
    "summary": "한국어 요약 분석 (반드시 존댓말/합쇼체로 작성)"
  }}
]""",
}


# ─────────────────────── TikTok 트렌드 분석 (Apify + OpenAI) ──────────────
@app.route('/api/trend/tiktok', methods=['POST'])
def api_trend_tiktok():
    """
    Apify clockworks/tiktok-scraper로 미국 뷰티 영상 수집
    → EXCLUDED_TAGS 필터링 후 Python Counter로 해시태그 중복 빈도 순위 추출
    → PLATFORM_PROMPTS['TikTok'] - Z세대 숏폼 바이럴 마케터 관점으로 gpt-4o-mini 분석
    """
    try:
        APIFY_TOKEN    = os.environ.get('APIFY_API_TOKEN', '')
        OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', '')

        if not APIFY_TOKEN:
            return jsonify({'error': '.env에 APIFY_API_TOKEN이 설정되어 있지 않습니다.'}), 400
        if not OPENAI_API_KEY:
            return jsonify({'error': '.env에 OPENAI_API_KEY가 설정되어 있지 않습니다.'}), 400

        body_data = request.get_json(force=True) or {}
        platform  = body_data.get('platform', 'TikTok')
        limit = 15 if platform == '전체' else 10

        from apify_client import ApifyClient
        from collections import Counter

        client = ApifyClient(APIFY_TOKEN)

        run_input = {
            "hashtags": ["skincare", "skincareroutine", "glowingskin"],
            "resultsPerPage": 1,
            "proxyConfiguration": {"useApifyProxy": True},
        }

        run   = client.actor('clockworks/tiktok-scraper').call(run_input=run_input)
        items = list(client.dataset(run['defaultDatasetId']).iterate_items())

        if not items:
            return jsonify({'error': 'Apify에서 TikTok 데이터를 가져오지 못했습니다.'}), 500

        counter     = Counter()
        video_texts = []

        for item in items:
            raw_tags = item.get('hashtags') or []
            for tag in raw_tags:
                if isinstance(tag, dict):
                    name = tag.get('name', '')
                elif isinstance(tag, str):
                    name = tag.replace('#', '')
                else:
                    continue
                name = name.lower().strip()
                if name and name not in EXCLUDED_TAGS:
                    counter[name] += 1
            text = item.get('text', '')
            if text:
                video_texts.append(text[:200])

        if not counter:
            return jsonify({'error': '수집된 영상에서 해시태그를 찾을 수 없습니다.'}), 500

        top_tags = counter.most_common(limit)

        from openai import OpenAI
        ai_client = OpenAI(api_key=OPENAI_API_KEY)

        tags_str   = ', '.join([f'{tag}({cnt}회)' for tag, cnt in top_tags])
        sample_txt = '\n'.join(video_texts[:20])

        prompt = PLATFORM_PROMPTS['TikTok'].format(
            tags_str=tags_str,
            sample_txt=sample_txt,
            limit=limit,
        )

        res = ai_client.chat.completions.create(
            model='gpt-4o-mini',
            messages=[{'role': 'user', 'content': prompt}],
            temperature=0.3,
            max_tokens=1500,
        )

        raw      = res.choices[0].message.content.strip()
        raw      = raw.replace('```json', '').replace('```', '').strip()
        keywords = json.loads(raw)
        keywords = sorted(keywords, key=lambda x: x.get('mentions', 0), reverse=True)

        return jsonify({
            'success':     True,
            'keywords':    keywords,
            'video_count': len(items),
            'platform':    'TikTok',
            'analyzed_at': datetime.now().strftime('%Y-%m-%d %H:%M KST'),
        })

    except Exception as e:
        return jsonify({'error': f'TikTok 분석 오류: {str(e)}'}), 500



# ─────────────────────── Instagram 트렌드 분석 (Apify + OpenAI) ────────────
@app.route('/api/trend/instagram', methods=['POST'])
def api_trend_instagram():
    """
    Apify apify/instagram-hashtag-scraper로 미국 K-뷰티 게시물 수집
    → EXCLUDED_TAGS 필터링 후 Python Counter로 해시태그 중복 빈도 순위 추출
    → PLATFORM_PROMPTS['Instagram'] - 비주얼·인플루언서 마케터 관점으로 gpt-4o-mini 분석
    """
    try:
        APIFY_TOKEN    = os.environ.get('APIFY_API_TOKEN', '')
        OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', '')

        if not APIFY_TOKEN:
            return jsonify({'error': '.env에 APIFY_API_TOKEN이 설정되어 있지 않습니다.'}), 400
        if not OPENAI_API_KEY:
            return jsonify({'error': '.env에 OPENAI_API_KEY가 설정되어 있지 않습니다.'}), 400

        from apify_client import ApifyClient
        from collections import Counter

        client = ApifyClient(APIFY_TOKEN)

        run_input = {
            'hashtags': ['skincareroutine', 'skincaretips', 'healthyskin'],
            'resultsLimit': 20,
            'proxyConfiguration': {'useApifyProxy': True},
        }

        run   = client.actor('apify/instagram-hashtag-scraper').call(run_input=run_input)
        items = list(client.dataset(run['defaultDatasetId']).iterate_items())

        if not items:
            return jsonify({'error': 'Apify에서 Instagram 데이터를 가져오지 못했습니다.'}), 500

        counter     = Counter()
        post_texts  = []

        for item in items:
            # 해시태그 수집
            raw_tags = item.get('hashtags') or item.get('taggedUsers') or []
            caption  = item.get('caption') or item.get('text') or ''

            # 캡션에서 해시태그 직접 파싱
            import re
            tags_in_caption = re.findall(r'#(\w+)', caption.lower())
            for name in tags_in_caption:
                name = name.strip()
                if name and name not in EXCLUDED_TAGS:
                    counter[name] += 1

            for tag in raw_tags:
                if isinstance(tag, dict):
                    name = tag.get('name', '') or tag.get('id', '')
                elif isinstance(tag, str):
                    name = tag.replace('#', '')
                else:
                    continue
                name = name.lower().strip()
                if name and name not in EXCLUDED_TAGS:
                    counter[name] += 1

            if caption:
                post_texts.append(caption[:200])

        if not counter:
            return jsonify({'error': '수집된 게시물에서 해시태그를 찾을 수 없습니다.'}), 500

        limit    = 10
        top_tags = counter.most_common(limit)

        from openai import OpenAI
        ai_client = OpenAI(api_key=OPENAI_API_KEY)

        tags_str   = ', '.join([f'{tag}({cnt}회)' for tag, cnt in top_tags])
        sample_txt = '\n'.join(post_texts[:20])

        prompt = PLATFORM_PROMPTS['Instagram'].format(
            tags_str=tags_str,
            sample_txt=sample_txt,
            limit=limit,
        )

        res = ai_client.chat.completions.create(
            model='gpt-4o-mini',
            messages=[{'role': 'user', 'content': prompt}],
            temperature=0.3,
            max_tokens=1500,
        )

        raw      = res.choices[0].message.content.strip()
        raw      = raw.replace('```json', '').replace('```', '').strip()
        keywords = json.loads(raw)
        keywords = sorted(keywords, key=lambda x: x.get('mentions', 0), reverse=True)

        return jsonify({
            'success':     True,
            'keywords':    keywords,
            'post_count':  len(items),
            'platform':    'Instagram',
            'analyzed_at': datetime.now().strftime('%Y-%m-%d %H:%M KST'),
        })

    except Exception as e:
        return jsonify({'error': f'Instagram 분석 오류: {str(e)}'}), 500


# ─────────────────────── 전체 플랫폼 통합 트렌드 (TikTok + Reddit) ─────────
@app.route('/api/trend/all', methods=['POST'])
def api_trend_all():
    """
    TikTok(Apify) + Reddit(Apify) 둘 다 수집 후 OpenAI로 통합 TOP 15 분석
    """
    try:
        APIFY_TOKEN    = os.environ.get('APIFY_API_TOKEN', '')
        OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', '')

        if not APIFY_TOKEN or not OPENAI_API_KEY:
            return jsonify({'error': '.env에 APIFY_API_TOKEN, OPENAI_API_KEY를 설정하세요.'}), 400

        from apify_client import ApifyClient
        from collections import Counter
        from openai import OpenAI

        tt_counter  = Counter()
        all_text    = ''
        tt_count    = 0
        rd_count    = 0

        # ── 1. TikTok 수집 ──────────────────────────────────────────────────
        try:
            tt_client = ApifyClient(APIFY_TOKEN)
            tt_run    = tt_client.actor('clockworks/tiktok-scraper').call(run_input={
                "hashtags": ["skincare", "skincareroutine", "glowingskin"],
                "resultsPerPage": 3,
                "proxyConfiguration": {"useApifyProxy": True},
            })
            tt_items = list(tt_client.dataset(tt_run['defaultDatasetId']).iterate_items())
            tt_count = len(tt_items)

            for item in tt_items:
                for tag in (item.get('hashtags') or []):
                    name = (tag.get('name','') if isinstance(tag, dict) else tag).lower().strip().replace('#','')
                    if name and name not in EXCLUDED_TAGS:
                        tt_counter[name] += 1
                if item.get('text'):
                    all_text += f"[TikTok캡션] {item['text'][:150]}\n"

            top_tt = tt_counter.most_common(20)
            if top_tt:
                tt_tags_str = ', '.join([f'#{t}({c}회)' for t, c in top_tt])
                all_text = f"[TikTok 핫 해시태그] {tt_tags_str}\n" + all_text

        except Exception as e:
            all_text += f"[TikTok 수집 오류: {e}]\n"

        # ── 2. Reddit 수집 (APIFY_API_TOKEN) ───────────────────────────────
        try:
            rd_client = ApifyClient(APIFY_TOKEN)
            rd_run    = rd_client.actor('trudax/reddit-scraper-lite').call(run_input={
                'startUrls': [{'url': 'https://www.reddit.com/r/AsianBeauty/new/'}],
                'maxItems': 30,
                'proxyConfiguration': {'useApifyProxy': True},
            })
            rd_items = list(rd_client.dataset(rd_run['defaultDatasetId']).iterate_items())
            rd_count = len(rd_items)

            for item in rd_items:
                title = item.get('title','')
                body  = item.get('text','') or item.get('selftext','') or ''
                if title or body:
                    all_text += f"[Reddit] {title} {body[:120]}\n"
        except Exception as e:
            all_text += f"[Reddit 수집 오류: {e}]\n"

        if not all_text.strip():
            return jsonify({'error': '수집된 데이터가 없습니다.'}), 500

        # ── 3. OpenAI 통합 분석 TOP 15 ─────────────────────────────────────
        ai_client = OpenAI(api_key=OPENAI_API_KEY)

        prompt = f"""너는 미국 스킨케어 시장을 분석하는 마케팅 전략가야.

[수집 데이터]
{all_text[:4000]}

[수행 작업 및 분석 가이드라인]
우리는 미국 시장에 '선세럼(Sun Serum)'을 런칭하려고 해. TikTok과 Reddit 데이터를 합산하여 미국에서 가장 핫한 스킨케어/선케어 트렌드 키워드 **TOP 15**를 도출해.

1. 절대적 객관성 유지 (할루시네이션 금지): 오직 제공된 데이터에서만 추출할 것.
2. 기존 선크림의 불만(White cast, Pilling 등)과 선호하는 텍스처(Lightweight, Glass skin 등)를 최우선으로 도출할 것.
3. 키워드 그룹핑: 유사어는 하나의 대표 키워드로 통합할 것.
4. 🚨 배제: Makeup, Color cosmetics 등 색조 단어와 Shipping 등 물류/구매 단어는 철저히 배제할 것.
5. 🚨 뻔한 단어 배제: 'Sunscreen', 'SPF', 'Sunblock' 등 자외선 차단제 단어 자체는 키워드 선정에서 아예 제외하고, 그로 인한 구체적인 피부 변화(효과/불만)나 특정 성분명에만 집중할 것.
6. 플랫폼 출처 표기: TikTok만→"tiktok", Reddit만→"reddit", 둘 다→"both"

[출력 형식 - 순수 JSON 배열만]
- 🚨 모든 'keyword'는 반드시 첫 글자를 대문자로 시작하는 Title Case 형식(예: Glass Skin, Vitamin C, Hydrating)으로 통일할 것.
[
  {{
    "keyword": "Glass Skin",
    "mentions": 숫자,
    "source": "tiktok 또는 reddit 또는 both",
    "summary": "이 키워드가 미국 스킨케어/선케어 시장에서 왜 핫한지, 선세럼 마케팅 관점에서 존댓말(합쇼체)로 한국어 2~3줄 분석"
  }}
]"""

        res = ai_client.chat.completions.create(
            model='gpt-4o-mini',
            messages=[{'role': 'user', 'content': prompt}],
            temperature=0.3,
            max_tokens=2500,
        )

        raw      = res.choices[0].message.content.strip().replace('```json','').replace('```','').strip()
        keywords = json.loads(raw)
        keywords = sorted(keywords, key=lambda x: int(x.get('mentions', 0) if x.get('mentions') else 0), reverse=True)

        return jsonify({
            'success':     True,
            'keywords':    keywords[:15],
            'platform':    '전체',
            'tt_count':    tt_count,
            'rd_count':    rd_count,
            'analyzed_at': datetime.now().strftime('%Y-%m-%d %H:%M KST'),
        })

    except Exception as e:
        return jsonify({'error': f'전체 분석 오류: {str(e)}'}), 500


# ─────────────────────── 페이지 라우터 ───────────────────────────────────
@app.route('/')
def index():
    return render_template('index.html', active_page='dashboard')

@app.route('/intelligence')
def intelligence():
    return render_template('intelligence.html', active_page='intelligence')

@app.route('/outreach')
def outreach():
    return render_template('outreach.html', active_page='outreach')

@app.route('/content')
def content():
    return render_template('content.html', active_page='content')

if __name__ == "__main__":
    print("\n🌿 Klear Intelligence Server 시작")
    print("   http://localhost:5000  ← 브라우저에서 열어주세요\n")
    app.run(debug=True, port=5000, threaded=True)