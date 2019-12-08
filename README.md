# del2rpp (Deluge to RPP)

Tool for converting [Synthstrom Audible Deluge](https://synthstrom.com/product/deluge/) song files (XML) to [REAPER](https://www.reaper.fm) project files (RPP).

![REAPER screenshot](example/screenshot.png)

## Usage
1. Clone or download the repository.

2. Install [pip](https://pip.pypa.io/en/stable/installing/).

3. Install [rpp](https://pypi.org/project/rpp/).

4. Run `del2rpp`:
```
python del2rpp.py example/SONGS/Test.XML out.rpp
```

5. Open `out.rpp` with REAPER.

## Issues

del2rpp is early software, and as such it will sometimes break. If you hit any issues, please [submit an issue](https://github.com/dcower/del2rpp/issues/new) and attach the song file that caused the issue.
