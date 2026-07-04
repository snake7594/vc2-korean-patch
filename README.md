# 전장의 발큐리아 2 한글패치 (Valkyria Chronicles 2 — Korean Translation Patch)

**대상 게임:** 戦場のヴァルキュリア2 ガリア王立士官学校 (PSP, `NPJH50145`, v1.01)
**패치 버전:** v23 · **형식:** xdelta3 (VCDIFF) · **크기:** 0.78 MB

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

패치 적용 후 결과물 ISO SHA1: `242566166785c3601457ecce954258e943da9dd8`

---

## 📥 적용 방법 (How to Apply)

원본 ISO에 `VC2_KoreanPatch_v23.xdelta`를 적용하면 한글패치된 ISO가 만들어집니다. 세 가지 방법 중 편한 것을 쓰세요.

### 방법 1 — Delta Patcher (GUI, 권장 / recommended)
1. [Delta Patcher](https://github.com/marco-calautti/DeltaPatcher/releases) 다운로드
2. **Original file** = 원본 ISO, **XDelta patch** = `VC2_KoreanPatch_v23.xdelta` 선택
3. **Apply patch** 클릭 → 한글패치 ISO 생성

### 방법 2 — 파이썬 (Python, 크로스플랫폼)
```bash
pip install pyxdelta
python apply_patch.py "원본.iso"
```
→ `VC2_Korean_v23.iso` 생성 (해시 자동 검증)

### 방법 3 — xdelta3 명령줄 (CLI)
```bash
xdelta3 -d -s "원본.iso" VC2_KoreanPatch_v23.xdelta VC2_Korean_v23.iso
```

만든 ISO는 **PPSSPP**(권장) 또는 CFW PSP 실기에서 실행하세요.

---

## ✅ 번역 범위 (What's Translated)

게임 폰트로 그려지는 **거의 모든 텍스트**를 한글화했습니다:

- **모든 스토리 대사·이벤트** (오프닝~엔딩, 전 이벤트)
- **미션 이름 · 브리핑 본문 · 전투 중 대사/말풍선 · 전투 튜토리얼**
- **캐릭터명 · 병과명 · 무기명 · 차량명 · 아이템명**
- **UI / 메뉴 / 시스템 메시지 / 난이도·세이브 화면**
- **아카데미 허브 메뉴 + 백과사전**

## ⚠️ 알려진 제한 (Known Limitations)

- **이미지에 구워진 글자:** 전적 화면 헤더, HUD 라벨 등 텍스처(그림) 안에 그려진 글자는 폰트 교체 범위 밖이라 일본어로 남습니다.
- **동영상(PMF) 자막:** 하드섭 재인코딩이 필요해 미번역입니다.
- 세이브 데이터 화면의 "データがありません"는 게임이 아니라 **PPSSPP 시스템 다이얼로그**입니다 (PPSSPP 언어 설정으로 변경).

## 🙏 크레딧 (Credits)

- 번역·제작 / Translation & hacking: [@snake7594](https://github.com/snake7594)
- 리버스 엔지니어링 보조 / RE assist: Claude (Anthropic)
- 도구 / Tools: [YACpkTool](https://github.com/Brolijah/YACpkTool), UMD-replace (CUE), [xdelta3](https://github.com/jmacd/xdelta)
- 참고 / Reference: VC2 러시아어 팬패치 (team MOSAS)

## ⚖️ 법적 고지 (Legal / Disclaimer)

이 패치는 팬이 무보수로 만든 **비공식 번역**이며 세가(SEGA) 및 어떤 권리자와도 무관합니다. 저작권은 원저작권자에게 있습니다. 이 저장소는 **게임 데이터를 일절 포함하지 않으며**, 패치는 이용자가 합법적으로 소유한 원본에만 적용할 수 있는 차분 파일입니다. 패치된 ISO나 게임 데이터를 재배포하지 마세요. 문제 시 관련 파일을 내리겠습니다.

*This is an unofficial, non-commercial fan translation, not affiliated with SEGA. No game data is included; the patch is a diff applicable only to a copy you legally own. Do not redistribute patched ISOs or game data.*
