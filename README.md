# Avatar Foundation cleanup — кисті, ніж та модульні поверхні

Робоча гілка: `feature/avatar-core-2-weapon-transitions`. ДО: `c2822a7`. Точка відновлення: `avatar-before-comprehensive-cleanup-c2822a7`.

Main `f70b7e5be63f6b85d895c6d5b259adbc30577b86`, гра, обидва rig JSON, оригінальні бази, донори, голови, зачіски та збереження не змінені. Зміни виконані тільки в дослідному Core/Lab і похідних ресурсах. Це результат для візуального погодження, а не production-ready інтеграція.

## Основний результат: рух ножа

Відмовились від inverse solve нерухомого ножа саме в melee. Рух задається від авторських кутів; ніж і хват мають одну матрицю. При стандартному параметрі 2 px повний розмах кисті/ножа 3,2°. Повний розмах ліктя: male1,20×1,12px, female0,91×0,91px; було male2,54×0,54px та female8,98×2,67px. Період 4000 мс. Початкові/кінцеві RGBA-кадри циклу збігаються. Instant cut збережено; старий morph не повернуто.

`Gallery/male-knife-motion-before-after.webp` та `female-knife-motion-before-after.webp` — синхронне порівняння. Це зменшені 20 кадрів/спрев’ю, не вимірювання FPS.

## Реєстр дефектів

|№|Пріоритет|Файл|Проблема|Доказ / причина|Правка|Статус|
|---|---|---|---|---|---|---|
|01|P1|`avatar-core/engine.mjs`|Білі смуги шиї / талії|Відтворено на CSS320/DPR1: α150 замість 253 біля шиї; CSS391,5: α229 біля талії.|Native941×1672 compositor, один display resize; спільна pinned mesh торса/одягу.|Виправлено в перевіреній матриці DPR 1/2.|
|02|P1|`avatar-core/assets/female/foundation-cleanup/rifle-right-complete.png`|Жіноче rifle-плече|Зарубки та вузькі провали зовнішнього краю.|Локальний похідний rifle-right-complete.png; збережена проксимальна реєстрація.|Технічний край покращено; художнє приймання потрібне.|
|03|P1|`avatar-core/assets/female/foundation-cleanup/rifle-right-complete.png`|Жіноче rifle-передпліччя|Трикутний виступ, обрізання знизу.|Локальна ретуш, повна поверхня і явне володіння переднім шаром.|Покращено; контур показано 1×/3×.|
|04|P1|`avatar-core/assets/female/foundation-cleanup/rifle-left-complete.png`|Жіноча опорна кисть rifle|Коричневі клапті над нігтями та по боках.|Локально відновлено шкіру, прибрано чужий матеріал.|Виправлено видимі клапті у контрольному рендері.|
|05|P1|`avatar-core/assets/male/foundation-cleanup/rifle-left-complete.png`|Чоловіча опорна кисть rifle|Чорні зубці й коричневі виступи.|Похідні rifle-left-arm/front/complete; чистий край пальців.|Виправлено видимі артефакти; хват потребує приймання.|
|06|P1|`avatar-core/assets/male/foundation-cleanup/rifle-right-complete.png`|Чоловіча права кисть rifle|Зубчастий темний залишок під долонею.|Локальна ретуш і незалежний предмет.|Виправлено контрольний край.|
|07|P1|`avatar-core/assets/male/foundation-cleanup/pistol-right-complete.png`|Чоловічий pistol-зап’ясток|Світла смуга, пунктирний край, чорний залишок.|Ретуш шва, відновлення справжнього негативного просвіту з оригіналу.|Покращено; крупний план збережено.|
|08|P1|`avatar-core/assets/male/foundation-cleanup/pistol-right-complete.png`|Чоловічий pistol-вказівний|Сумнівні довжина/перехід пальця.|Без зміни кісток; локально уточнена поверхня.|Не оголошено повністю закритим: потрібне художнє рішення.|
|09|P1|`avatar-core/assets/female/foundation-cleanup/pistol-right-complete.png`|Жіночий pistol-контур|Темна обводка, світлий клин і грубе зап’ястя.|Локальна ретуш лише похідної руки; природний просвіт збережений.|Покращено, показано без предмета.|
|10|P1|`review/avatar-foundation-cleanup/Evidence/art-export.json`|Фактура жіночих рук|Жили / об’єм відрізняються від idle.|Невелика тонова гармонізація, без розмиття тіла.|Частково покращено; художнє приймання відкрите.|
|11|P1|`avatar-core/assets/male/foundation-cleanup/melee-right-complete.png`|Чоловічий melee|Різка фактура й монтажний край кисті.|Ретуш похідного сегмента; базова анатомія та проєкція збережені.|Край покращено; фактура не сертифікована як фінальна.|
|12|P1|`avatar-core/assets/female/foundation-cleanup/melee-right-complete.png`|Жіночий melee|Східчастий хват, темні залишки.|Локально відновлена повна кисть і розділені шари.|Покращено; показано без ножа й із ножем.|
|13|P1|`review/avatar-foundation-cleanup/Evidence/prop-export.json`|Шкіра в weapon PNG|Донорська шкіра й отвори в предметах.|Використані цілі наявні чисті props з точно збереженими афінними перетвореннями.|Виправлено розділення ресурсів; інші форми зброї не сертифіковані.|
|14|P1|`tools/prepare-foundation-cleanup.py`|Матові ореоли рук|Темні краї й слабкий шум.|Вибіркове очищення alpha≤16 поза 2px від ядра; RGB fringe від найближчої непрозорої шкіри.|Активні ресурси пройшли критерії; не загальна ерозія.|
|15|P1|`avatar-core/engine.mjs`; `avatar-core/assets/diagnostics/config.json`|Різні деформації одягу|Torso affine проти pinned mesh, інші UV рук.|Спільна torso mesh; poseSources для діагностичних рукавів/рукавичок.|Перевірено діагностикою, старий довільний одяг не сертифіковано.|
|16|P1|`avatar-lab/index.html`; `docs/avatar-weapon-attachments.md`|85/115% предметів|Другий контакт не перекалібровується.|Залишено явно діагностичними розмірами;100% — калібрований профіль.|Обмеження задокументовано; універсальні хвати не реалізовані.|
|17|P1|`avatar-core/assets/diagnostics/config.json`|Гардероб / майбутні скіни|Реального garment integration немає.|8 типів контрольного одягу,2 відтінки skin probe, обидві статі й пози.|Діагностика підтверджена; реальний гардероб не заявляється.|
|18|P2|`tools/capture-foundation-dense.py`; `tools/record-foundation-raf.py`|Розріджені відео|Старі 20 відео повторно декодовані; не доказ 60fps.|Точні 241RGBA-кадр на випадок + нові реальні RAF відео з PTS.|Покриття покращено; actual FPS див. JSON, не тест фізичного пристрою.|
|19|P2|`base_male.png`; `avatar-core/assets/male/foundation-cleanup/base-runtime.png`|Alpha-шум бази / регресія|Захищений base_male.png має слабкий шум; baseline273/274.|Похідні runtime-копії:4281 піксель,α≤3, решта RGBA незмінні.|Runtime очищено; старий тест оригіналу навмисно залишається невдалим.|
|20|P2|`docs/avatar-weapon-attachments.md`|Застаріла документація|Активні жіночі бойові руки вже підключені.|Оновлено актуальний опис формату і фактичну карту ресурсів.|Виправлено в поточному звіті; старі історичні звіти не підмінено.|
|21|P1|`avatar-core/relaxed-melee.mjs`; `avatar-core/engine.mjs`|Ніж / надмірний рух ліктя|Pinned grip + IK: ніж майже нерухомий, female elbowspan8,98px.|Forward upper±0,035°,fore±0,12°,hand±1,6°; ніж успадковує кисть.|Виправлено обидві статі;4000 мс, instant cuts, grip error<1e-6.|
|22|P1|`avatar-core/assets/male/foundation-cleanup/rifle-weapon.png`; `avatar-core/assets/female/foundation-cleanup/rifle-weapon.png`|Приклади male/female foundation-cleanup/rifle-weapon.png|Male:38,74px до ліктя при межі 35px; female:146,17px до плеча при межі 60px.|Контакти обох кистей збережені; окремий контур/довжина приклада потребують адаптації.|Відкрито. Тест не послаблено.|

## Ресурси й відтворення

Вісім локальних ретушей рук збережено в Edits; точні джерельні crops у Before. Не генерувався новий цілий персонаж. Пайплайн `tools/prepare-foundation-cleanup.py` зберігає оригінальні реєстрації/риг, експортує arm/front/complete і чисті предмети. Жіночі накладки 941×1672; чоловічі cropped PNG відповідають rig.mesh.bounds. Параметри/хеші: Evidence/art-export.json, prop-export.json, runtime-alpha-cleanup.json. Альфа переднього шару відокремлює дистальну кисть від передпліччя.

Завершена рука малюється один раз. Передні пальці застосовуються до окремого weapon-group через source-atop тільки в межах предмета; відкритий край шкіри не подвоюється. Тест порівнює всі RGBA-байти поза предметом при visible/hidden.

Нові runtime-матові копії чоловіка не змінюють жодного іншого RGBA-байта. Оригінальні PNG і суворий старий поріг збережено. Ресурс ножа взято з наявного clean prop, не з донорського повнокадрового зображення.

## Поточна регресія

JavaScript: **119/119**. Python: див. точні поля `Evidence/final-tests/summary.json`: `{"total": 288, "ran": 288, "passed": 284, "failure_ids": ["tests.test_paper_doll_audit.AuditAssetTests.test_no_remote_faint_haze_or_detached_low_alpha_specks", "tests.test_weapon_pass.WeaponPassBrowserTests.test_rifle_and_pistol_match_their_current_calibrated_art_bind", "tests.test_avatar_polish.PolishBrowserTests.test_supported_pistol_and_combat_wrists_do_not_fold_backwards", "tests.test_male_lobby.LobbyBrowserTests.test_relaxed_rifle_elbows_stock_contacts_and_face_clearance"], "skipped": 0, "all_passed": false, "execution": "serialized asset-mutating preparation followed by read-only bounded shards; no retries"}`.

Нативні lossless: **4338** кадрів у 18 випадках. 241 кадр включно 0..4000 мс з кроком 1000/60 мс. `.avframes` зберігає точні RGBA-байти кожного кадру, включно з невидимими RGB; кожний SHA перевірено після декодування. `ViewFrames.html` відкриває їх автономно; `tools/verify-foundation-frames.py` незалежно декодує/експортує PNG.

Нові живі записи: **10** WebM, справжній requestAnimationFrame/MediaRecorder; actual timestamps та max_gap_seconds — `Evidence/real-raf-motion.json`. Не заявляється стабільні 60fps. Прозорі dense-кадри перевіряються на 5 фонах через viewer; додаткові реальні direct-background перевірки окремо в browser-probes.json. Це не 19280 окремих Canvasрендерів.

Старий пакет: усі 288 вхідних SHA звірені. 268 зображень переглянуто оглядово з цільовими збільшеннями, не вручну кожний піксель.20 відео незалежно повторно декодовані; PTS і кількість у old-videos-independent-decode.json. Проміжні невдалі/перервані запуски збережено в Evidence; вони не зараховані до фінального прогону. В одному ранньому тесті помилково вимагалиα255, хоча вихідна шкіраα252–253; критерій тепер відносний до незмінного джерела. Контактні тести мають незалежні вихідні RGBA/UV; стара female pistol мала blended weights і жодної rigidhandкомірки, тому тепер перевіряються також математично спроєктовані UVпікселі. Старі контрольні еталони не підмінені.

## Обмеження

Експеримент пакетного переднього шару відхилено: виграшу часу не було, змінилися крайові RGBA. Початковий комітований compositor відновлено побайтно. Вимірювання під паралельним тестовим навантаженням збережені, це не FPS реального пристрою. Також raw-читання кадрів виявилось повільнішим за PNG; фінальна зйомка використовує PNG.

Суворі перевірки rifle stock contact не проходять (male38,74px до ліктя при межі 35px; female146,17px до плеча при межі 60px). Female rifle stock contact не проходить для нового чистого предмета: відстань до плеча 146,17px при порозі 60px. Її не послаблено. Потрібен окремий адаптований female rifle-weapon.png із правильним контуром приклада; це відкрита проблема, незалежна від виправленого руху ножа.

Потрібне художнє погодження пальців/фактури, особливо male pistol index та female бойових передпліч. Для ручного допрацювання використовувати `avatar-core/assets/{male,female}/foundation-cleanup/{pose}-{side}-complete.png` і відповідні front/arm через пайплайн; не малювати поверх оригінальної бази.

Перевірено Chromium у Linux. Firefox/WebKit і фізичні пристрої недоступні; вузький viewport — емуляція. Реальний гардероб не інтегровано: перевірено лише діагностичні gridgarments та наявні compatibilityтести. Не доведена сумісність будь-якого майбутнього одягу/будь-якої зброї. Гру й GitHubPages не публікували й не змінювали. Опублікований буде лише автономний review-архів окремим tag.

## Відкриття

Для повторної зйомки у свіжому репозиторії підготуйте `../avatar-foundation-baseline` на `c2822a7` (окремий detached worktree). Великі generated Gallery/Evidence зберігаються у хешованому review-архіві, не дублюються в історії робочої гілки;8beforePNG для Lab і критичні маски/маніфести залишаються в Git. Невдалі перевірки не видалені: усі поточні логи і фактичні failure_ids включені в архів.

Pipeline/Source запускаються у вихідному репозиторії; Runtime — точні ресурси для ревізії, не окремий інсталятор гри. Повністю розпакувати ZIP. Відкрити Report.html браузером, Avatar-Lab.html — інтерактивний реальний Lab без сервера. Вибрати стать → melee → breathing. Передні пальці, ніж, діагностичний одяг і 2skinprobeвідтінки перемикаються незалежно. Нативні кадри: ViewFrames.html → вибрати файл Gallery/Dense/*.avframes.
