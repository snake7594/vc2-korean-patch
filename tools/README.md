# Tools — VC2 (PSP) 포맷 역분석 & 패치 도구

VC2(그리고 대부분의 SJIS 기반 일본 PSP 게임)의 텍스트를 추출·번역·주입하기 위한
파이썬 모듈들입니다. 자세한 포맷 설명은 [`../docs/TECHNICAL.md`](../docs/TECHNICAL.md).

> ⚠️ **게임 데이터는 포함되어 있지 않습니다.** 이 도구들은 **본인이 소유한 원본 ISO에서
> 직접 추출한 파일**에 대해 동작합니다. 코드 상단의 경로(`C:/vc2work/ODIN_fresh` 등)와
> 한글 TTF 경로는 저자 환경 기준이니 본인 환경에 맞게 바꿔 쓰세요.

## 필요 도구
- Python 3, `pip install pillow pyxdelta`
- 한글 TTF (예: 서울한강체 등 자유 사용 폰트) — `vc2_hangul_patch.py`에서 지정
- [YACpkTool](https://github.com/Brolijah/YACpkTool) (+CpkMaker.dll), UMD-replace (CUE)

## 모듈

| 파일 | 설명 |
|---|---|
| `vc2crypt.py` | CPK 파일 XOR 암호. `decrypt_resource(raw,0)` / `encrypt_resource(key16,body)` / `find_resources(raw)`. 대칭이라 복호화=암호화. |
| `mtpa_edit.py` | MTPA 대사 파싱/편집. `parse`, `records`, `get_payloads`, **`rebuild_inplace(body,{rec:payload})`**(안전한 in-place 주입). |
| `vc2_font2b.py` | BF1 전각(MFNT#2, 2bpp) 글리프 read/write. `glyph_offset(code)`, `read_glyph`, `write_glyph`. |
| `vc2_hangul_patch.py` | 한글 TTF를 2bpp로 렌더(`raster2bpp`) + wansung 매핑 빌드 헬퍼. |
| `wansung_encode.py` | 한국어 텍스트 → wansung 바이트. `encode_ko(text,mapping,nl)`, `build_mapping`, `build_font`, `collect_syllables`. |
| `mxe_tool.py` | MXE(MXEN/MXEC) 롤링 XOR 복호/암호 + 문자열 런 추출. **롤 영역 = datasize까지**(POF0/ENRS 보존). `decrypt_file`/`encrypt_file`/`extract_runs`. |
| `nested_runs.py` | 비표준 컨테이너 MTP를 위한 **동일 길이 SJIS 런 치환**(구조 무손상). |
| `boottest.py` | PPSSPP로 ISO 부팅 후 에뮬 RAM 매직 개수로 부팅 성패 자동 판정(≈845 정상). |

## 최소 예시

```python
import vc2crypt as vc, mxe_tool as mx

# 1) MXE 한 파일의 일본어 문자열 뽑기
plain, meta = mx.decrypt_file(open('MISSION_001.MXE','rb').read())
for r in mx.extract_runs(plain, meta['start'], meta['end']):
    print(hex(r['start']), r['text'])

# 2) 편집 후 재암호화 (동일 길이로 buf[start:start+nbytes] 교체했다고 가정)
open('MISSION_001.MXE','wb').write(mx.encrypt_file(bytes(buf), meta))
```

전체 파이프라인(추출→번역→폰트→주입→재패킹→xdelta)은
[`../docs/TECHNICAL.md`](../docs/TECHNICAL.md) §8을 참고하세요.

## 라이선스 / 주의
- 이 코드는 포맷 상호운용(interoperability)을 위한 역분석 도구입니다.
- 게임 저작물(스크립트·폰트·에셋)은 세가(SEGA)의 것이며 여기에 포함되지 않습니다.
- 추출한 게임 데이터나 패치된 ISO를 재배포하지 마세요.
