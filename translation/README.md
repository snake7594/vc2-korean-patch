# Translation data — 대사를 직접 바꾸기 (edit the dialogue yourself)

번역문을 직접 수정하고 패치를 다시 만들 수 있습니다. 오역 수정, 문체 변경, 다른 번역본
제작 등에 쓰세요.

> ⚠️ 여기에는 **게임 데이터가 없습니다.** 재빌드하려면 **본인 소유의 원본 ISO에서 추출한
> ODIN.CPK 파일**과 한글 TTF가 필요합니다. `jp`(일본어 원문)는 참조·대조용이며 저작권은
> 세가(SEGA)에 있습니다. 추출 데이터·패치 ISO를 재배포하지 마세요.

## 파일

- **`translations.json`** — 편집 대상. `ko`(한국어)만 고치면 됩니다.
- **`rebuild.py`** — 수정한 `translations.json`으로 패치 파일을 다시 만드는 스크립트.

## translations.json 구조

```jsonc
{
  "records": {                       // 표준 MTPA 대사/UI (레코드 단위)
    "MTPA_EV10002.MTP": {
      "15": { "jp": "ユベール…です。", "ko": "위베르…입니다." },
      ...
    }
  },
  "runs": {                          // MXE(이름·브리핑)·중첩·시스템 (오프셋 단위)
    "MISSION_001.MXE": [
      { "jp": "メルフェア市に…", "ko": "멜페어 시에…", "src": "mxe", "start": 1318, "nbytes": 98 },
      ...
    ]
  }
}
```

### 편집 규칙
- **`ko` 값만** 바꾸세요. `jp`·`src`·`start`·`nbytes`는 건드리지 마세요.
- **길이 제한**: 한국어가 원래 칸(`nbytes`)에 들어가야 합니다. 대략 **한글 1자=2바이트,
  ASCII·공백=1바이트**. 너무 길면 재빌드가 자동으로 뒤를 잘라 맞춥니다(잘리기 싫으면 짧게).
- **줄바꿈 `\n`**, 색상 마크업 `@fcRRGGBBAA … @fci`, 치환자 `%s %d`, 시스템 메시지의
  `{MS}`(메모리스틱 아이콘)는 **그대로 유지**하세요.
- 폰트에 없던 새 음절을 써도 재빌드가 자동으로 폰트에 추가합니다(제한 없음).
- 일본어(가나/한자)는 남기지 마세요 — 한글·ASCII·기본 문장부호만.

## 재빌드 방법

```bash
pip install pillow pyxdelta
python rebuild.py  <ODIN_추출폴더>  <한글폰트.ttf>  [출력폴더]
```

1. 원본 ISO에서 `ODIN.CPK`를 [YACpkTool](https://github.com/Brolijah/YACpkTool)로 폴더에 추출
   → 그 폴더 경로가 `<ODIN_추출폴더>`.
2. 위 명령 실행 → `출력폴더`(기본 `patched_out/`)에 **원본과 동일 크기의 패치 파일**이 생성됨.
3. 그 파일들을 ODIN 추출 폴더에 덮어쓰고 → `YACpkTool 폴더 ODIN2.CPK`로 재패킹
   → `UMD-replace game.iso PSP_GAME/USRDIR/ODIN.CPK ODIN2.CPK`로 ISO에 주입.
   (자세한 과정: [`../docs/TECHNICAL.md`](../docs/TECHNICAL.md) §8)

모든 출력 파일이 원본과 **동일 크기**라, 원본 CPK를 in-place로 덮어써 배포용 xdelta를
작게 뜰 수도 있습니다.

## 팁
- 특정 대사 찾기: `translations.json`에서 `jp` 원문이나 기존 `ko`로 검색.
- 큰 파일이라 텍스트 에디터에서 열 때 UTF-8로 저장하세요.
