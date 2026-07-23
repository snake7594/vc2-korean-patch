# 전장의 발큐리아 2 한글패치 (Valkyria Chronicles 2 — Korean Translation Patch)

![Valkyria Chronicles 2](screenshots/title.png)

**대상 게임:** 戦場のヴァルキュリア2 ガリア王立士官学校 (PSP, `NPJH50145`, v1.01)
**패치 버전:** v36 · **형식:** xdelta3 (VCDIFF) + DLC 드롭인 zip · **크기:** 실기용 65 MB / 에뮬용 54 MB / DLC 3.3 MB

> ### 🎮 v36 = 본편 + **DLC 완전 한글패치** (한 번에)
> | 구성 | 대상 | 파일 | 적용 |
> |---|---|---|---|
> | **본편 (실기용)** | 실제 PSP (CFW) | `VC2_KoreanPatch_v36_hw.xdelta` | ISO에 xdelta 적용 |
> | **본편 (에뮬용)** | PPSSPP | `VC2_KoreanPatch_v36_emu.xdelta` | ISO에 xdelta 적용 |
> | **DLC (공용)** | 실기 + PPSSPP | `VC2_KoreanPatch_v36_DLC.zip` | DLC 폴더에 압축 해제 |
>
> **v36 = 작전 브리핑 줄 잘림 수정.** 반각 대문자(Ｆ組의 F 등)가 폰트 폭 표의 잘못된 값으로 과도하게 넓게 렌더돼 브리핑이 세로로 밀리며 첫 줄이 잘리던 문제를, 원문처럼 **전각 문자**로 바꾸고 넘치는 줄을 재배치해 해결했습니다. (v35의 콘텐츠 목록 전체 한글화 포함.) **본편 ISO 패치는 v32~v35와 완전히 동일**하므로, 이미 적용했다면 ISO는 그대로 두고 **DLC zip만 새로 설치**하면 됩니다.
>
> 본편 동영상 자막은 v32와 동일: 실기용은 **Sony 정품 인코더**, 에뮬용은 **x264**. 텍스트·이미지·타이틀 한글화는 두 버전 동일합니다.

일본어판 PSP 게임을 한국어로 번역하는 **비공식 팬 번역 패치**입니다. 게임에 내장된 폰트의 한자 자리에 한글을 넣는 방식(wansung)으로, 별도 폰트 없이 게임 안에서 한글이 그려집니다.

> ⚠️ **이 저장소에는 게임 데이터가 들어 있지 않습니다.** 패치는 *차분(diff)* 파일이라 **본인이 합법적으로 소유한 원본 ISO**가 있어야만 적용·실행됩니다. 원본 없이는 아무 쓸모가 없습니다.

---

## ⚠️ 준비물 (Requirements)

본인이 직접 덤프했거나 소유한 아래 ISO가 필요합니다. **해시가 정확히 일치해야** 패치가 적용됩니다.

| 항목 | 값 |
|---|---|
| DISC ID | `NPJH50145` (일본판, v1.01) |
| 파일 크기 | `1,120,927,744` bytes |
| MD5 | `583a022cf364e93020abf13d69a76ef8` |
| SHA1 | `809a6a106aaf39d3a5aa18b5d7b0f7b70b6e1d65` |

패치 적용 후 결과물 ISO SHA1: **실기용** `a7bb9739c748fc1bd2b8773d8e00332fd4fc98ea` · **에뮬용** `59f1ec0a61912223115258a2efb09821f74bc14e`

---

## 📥 적용 방법 (How to Apply)

먼저 **[Releases](../../releases/latest)** 페이지에서 자기 환경에 맞는 패치를 내려받으세요 — 실제 PSP는 **`VC2_KoreanPatch_v36_hw.xdelta`**, PPSSPP는 **`VC2_KoreanPatch_v36_emu.xdelta`** (용량이 커서 저장소가 아닌 릴리스에 첨부). 이 패치를 원본 ISO에 적용하면 한글패치 ISO가 만들어집니다. 아래 `PATCH` 자리에 받은 파일명을 넣으세요. **DLC까지 쓰려면 아래 「🎁 DLC 설치」 절을 이어서 진행하세요.**

### 방법 1 — Delta Patcher (GUI, 권장 / recommended)
1. [Delta Patcher](https://github.com/marco-calautti/DeltaPatcher/releases) 다운로드
2. **Original file** = 원본 ISO, **XDelta patch** = 받은 `.xdelta` 선택
3. **Apply patch** 클릭 → 한글패치 ISO 생성

### 방법 2 — 파이썬 (Python, 크로스플랫폼)
```bash
pip install pyxdelta
python apply_patch.py "원본.iso"      # 폴더에 둔 .xdelta를 자동 감지·검증
```

### 방법 3 — xdelta3 명령줄 (CLI)
```bash
xdelta3 -d -s "원본.iso" PATCH.xdelta VC2_Korean.iso
```

실기용은 **CFW PSP**에서, 에뮬용은 **PPSSPP**에서 실행하세요.

---

## 🎁 DLC 설치 (real PSP / PPSSPP)

DLC 한글패치는 ISO 패치가 아니라 **DLC 폴더를 통째로 교체**하는 방식입니다. **[Releases](../../releases/latest)** 에서 **`VC2_KoreanPatch_v36_DLC.zip`** 을 받으세요. 압축 안에는 `PSP/GAME/NPJH50145/` 구조가 그대로 들어 있습니다.

> ⚠️ **본편 한글패치(v32 이상)를 먼저 적용해야 합니다.** DLC에는 폰트가 없어 **본편 패치의 한글 폰트를 공유**합니다. 원본 일본판과 함께 쓰면 글자가 깨진 한자로 보입니다.
>
> ℹ️ 이 DLC는 **복호화된 형태**(제공 원본과 동일)라 별도 라이선스(`.rif`/`.rap`) 파일이 필요 없습니다. 기존에 DLC가 정상 동작하던 환경이면 그대로 동작합니다.

### PPSSPP
1. PPSSPP 실행 → **설정 → 시스템 → "메모리스틱 폴더 열기"** (Open Memstick Folder)
2. 열린 폴더(memstick)에 zip을 **그대로 압축 해제** → `memstick/PSP/GAME/NPJH50145/` 로 들어갑니다.
   - 이미 원본 DLC가 있으면 **덮어쓰기** (원본 백업 권장).
3. 게임(한글패치 ISO) 실행 → 미션 목록에서 DLC 미션이 한글로 표시됩니다.

> memstick 위치(참고): 설치 없이 쓰는 Windows판은 PPSSPP 폴더 아래 `memstick/`, Mac/Linux는 `~/.config/ppsspp/PSP/`.

### 실제 PSP (CFW)
1. PSP를 PC에 USB로 연결 (또는 메모리스틱 리더).
2. zip을 메모리스틱 **루트에 그대로 압축 해제** → `ms0:/PSP/GAME/NPJH50145/` 로 들어갑니다.
   - PSP Go 내장 메모리는 `ef0:/PSP/GAME/NPJH50145/`.
   - 이미 원본 DLC가 있으면 **덮어쓰기** (원본 백업 권장).
3. 한글패치 ISO(실기용, `_hw`)를 CFW로 실행 → 미션 목록에서 DLC가 한글로 표시됩니다.

폴더 구조 예시:
```
ms0:/PSP/GAME/NPJH50145/
├─ PARAM.PBP
├─ DL11/  ├─ DL11.EDAT   └─ DL11_DATA.EDAT
├─ DL15/  ...
└─ DL2A/  ...
```

**DLC 번역 범위 (v35 = 전체):** 22개 미션의 **콘텐츠 목록 제목**(공략전 연습 대F조, 뒷과정 수료시험, 격전!…EX, 남격갱 등) · **하단 설명 · 장소/승리조건/제한** · **미션명·적 에이스명·보상 무기명·브리핑** · **DLC 무기 정보**(헤르보르, 힐드, 흐리스트 등 발키리 무기) · **스토리 미션 「멜페어의 위기」메뉴** · **보너스 스티커**(알렉시스/마가리). (맵·수치 데이터, 개발용 내부 라벨은 비노출이라 제외.)

---

## ✅ 번역 범위 (What's Translated)

게임 폰트로 그려지는 **거의 모든 텍스트**를 한글화했습니다:

- **모든 스토리 대사·이벤트** (오프닝~엔딩, 전 이벤트)
- **미션 이름 · 브리핑 본문 · 전투 중 대사/말풍선 · 전투 튜토리얼**
- **캐릭터명 · 병과명 · 무기명 · 차량명 · 아이템명**
- **UI / 메뉴 / 시스템 메시지 / 난이도·세이브 화면**
- **아카데미 허브 메뉴 + 백과사전**
- **타이틀 화면** (v27): 로고·부제·「Press START button」 등 타이틀 텍스처 한글화
- **동영상 한국어 자막** (v32부터 실기·에뮬 모두): 일본어 자막이 있는 영상 전부(오프닝 프롤로그, 챕터/스토리 회상, 캐릭터 소개, 엔딩 프로필) — 원문을 가리지 않게 위/아래로 배치한 흰 글자+검은 테두리 하드섭. 실기용은 Sony 정품 인코더, 에뮬용은 x264로 인코딩.
- **이미지에 구워진 텍스트 일부** (v26): 건강 경고 화면, 전투 결과 화면 라벨(전적 보고서·전투 성적·부대명·기본 전적·클리어 평가·턴/명/대/개 등), 세이브/인스톨 데이터 아이콘
- **DLC 전체** (v35, 별도 zip): 콘텐츠 목록의 모든 제목·설명 + 22개 미션(미션명·에이스명·무기명·브리핑) + DLC 무기 정보 + 스토리 미션 메뉴 + 보너스 스티커 (설치는 위 「🎁 DLC 설치」 절 참고)

## ⚠️ 알려진 제한 (Known Limitations)

- **실기용/에뮬용 구분:** 자막 동영상은 재인코딩이 필요한데, x264로 재인코딩한 H.264는 **실기 PSP Media Engine이 거부**합니다(PPSSPP는 정상). 실기용은 **Sony 정품 CLI 인코더(PSMF Encoder)**로 원본과 동일 규격의 스트림을 만들어 해결했습니다. 반드시 환경에 맞는 버전을 쓰세요(실기=hw, PPSSPP=emu).
- **이미지에 구워진 글자(일부):** 전투 HUD 라벨 등 일부 텍스처 글자는 일본어로 남습니다. 주요 화면(타이틀·경고·전투 결과·세이브 아이콘)은 두 버전 모두 한글화.
- **엔딩 크레딧 영상:** 실제 제작진·성우 이름이라 원본(일본어) 유지.
- 세이브 데이터 화면의 "データがありません"는 게임이 아니라 **PPSSPP 시스템 다이얼로그**입니다 (PPSSPP 언어 설정으로 변경).

## 🛠️ 직접 해보기 · 기술 자료 (Do-it-yourself / Technical materials)

이 저장소에는 **포맷 역분석 도구와 상세 기술 문서**가 함께 들어 있어, 다른 SJIS 기반
일본 게임을 패치하거나 이 패치를 재현·확장할 수 있습니다.

- **[`docs/TECHNICAL.md`](docs/TECHNICAL.md)** — CPK 암호, BF1 폰트, MTPA/MXE 포맷,
  wansung 한글 치환법, ★MXE 롤-암호화 영역 함정, 전체 파이프라인, 함정·교훈까지 총정리.
- **[`tools/`](tools/)** — 파이썬 역분석·패치 모듈(`vc2crypt`, `mxe_tool`, `mtpa_edit`,
  `vc2_font2b`, `wansung_encode`, `nested_runs`, `boottest`) + 사용법.
- **[`translation/`](translation/)** — **대사를 직접 바꿀 수 있는 번역 데이터**
  (`translations.json`, 편집 가능한 `{jp, ko}` 16,000여 항목) + 재빌드 스크립트
  (`rebuild.py`). 오역 수정·문체 변경·다른 번역본 제작에 쓰세요.

> 도구·재빌드는 **본인이 소유한 원본 ISO에서 추출한 파일**에 대해 동작하며, 게임 데이터는
> 포함하지 않습니다. `git`으로 clone 후 `docs/TECHNICAL.md`부터 읽으세요.

> ※ 배포 패치(`VC2_KoreanPatch_v36_hw.xdelta` 실기용 / `_emu.xdelta` 에뮬용 / `_DLC.zip` DLC)는
> 저장소가 아니라 **Releases**에 첨부되어 있습니다. 받아서 `apply_patch.py`와 같은 폴더에 두세요.

```
vc2-korean-patch/
├─ apply_patch.py               # 파이썬 적용 스크립트 (해시 검증)
├─ docs/TECHNICAL.md            # 기술 문서
├─ tools/                       # 역분석·패치 도구 + README
│  └─ dlc/                      # DLC 추출·주입 도구 + 번역 원본(dlc_ko.py)
├─ translation/                 # 편집 가능한 번역 데이터 + rebuild.py
│  └─ dlc_translations.json     # DLC JP↔KO 대조표 (186쌍)
└─ screenshots/
```

## 🙏 크레딧 (Credits)

- 번역·제작 / Translation & hacking: [@snake7594](https://github.com/snake7594)
- 리버스 엔지니어링 보조 / RE assist: Claude (Anthropic)
- 도구 / Tools: [YACpkTool](https://github.com/Brolijah/YACpkTool), UMD-replace (CUE), [xdelta3](https://github.com/jmacd/xdelta)
- 참고 / Reference: VC2 러시아어 팬패치 (team MOSAS)

## ⚖️ 법적 고지 (Legal / Disclaimer)

이 패치는 팬이 무보수로 만든 **비공식 번역**이며 세가(SEGA) 및 어떤 권리자와도 무관합니다. 저작권은 원저작권자에게 있습니다. 이 저장소는 **게임 데이터를 일절 포함하지 않으며**, 패치는 이용자가 합법적으로 소유한 원본에만 적용할 수 있는 차분 파일입니다. 패치된 ISO나 게임 데이터를 재배포하지 마세요. 문제 시 관련 파일을 내리겠습니다.

*This is an unofficial, non-commercial fan translation, not affiliated with SEGA. No game data is included; the patch is a diff applicable only to a copy you legally own. Do not redistribute patched ISOs or game data.*
