## KoreanInputProcessor for Sublime Text 4

Helps Korean (Hangul) keyboard input for Sublime Text 4 DEV

Windows Sublime Text 4 DEV에서 한글 문자 입력을 지원하는 패키지입니다. IME에서 입력 문자가 올바른 위치에 표시되지 않는 문제를 어느 정도 해결할 수 있습니다.

Sublime Text 4 DEV에서 기존에 널리 사용되고 있는 IMESupport 패키지가 동작하지 않고 있습니다. 또한, 초성 중성 종성 입력으로 하나의 글자가 완성된 후 커서가 이동하지 않는 문제가 더해졌습니다. KoreanInputProcessor는 이를 해결하기 위한 패키지입니다. 기존 Sublime Text 2, 3 에서는 IMESupport 패키지의 사용을 추천합니다.

Windows IME hook을 사용하는 IMESupport와는 완전히 다른 방식으로 구현되었습니다. 한글 초성 중성 종성 입력 문자를 버퍼에 저장하고 이를 합성하여 View에 직접 렌더링 하도록 하였습니다. 한글 문자 합성 라이브러리인 hgtk의 설치(`pip install hgtk`)가 필요합니다.

### Known issues

영역 선택 후 한글 입력 시 정상 동작하지 않는 문제가 있습니다.
