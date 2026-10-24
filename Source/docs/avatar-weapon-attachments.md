# Avatar Core: окремий предмет і варіанти хвату

Це дослідний Avatar Lab, не інтеграція в main/гардероб. Початкові PNG не змінюються. Дихання — 4000 мс; чоловічі пози перемикаються instant cut.

## Чинний формат

`avatar-core/weapons.json` містить спільні класи; `avatar-core/male-preview.json.weapons` — чоловічі художні тестові ресурси. `weapon-controller.mjs` застосовує їх до окремих `rigs/{gender}_rig.json`. В обох персонажів той самий контролер, але різні плечі, довжини кісток, пози й контактні точки. Координати чоловіка не є жіночим шаблоном.

| Поле | Значення |
|---|---|
| `image` | PNG предмета, без запечених пальців |
| `size` | Розмір полотна PNG |
| `primary` | Основний хват у пікселях ресурсу |
| `support` | Додаткова точка для другої руки; `null` для одноручної пози |
| `scale` | Рівномірний масштаб предмета |
| `angle` | Додатковий кут у градусах |
| `offset` | Поправка точок ресурсу |
| `order` | Порядок предмета; у поточному Core предмет малюється між заднім і переднім проходом рук |
| `stock`, `trigger` | Контрольні точки для перевірки постановки; самі не пересувають плечі |

Поза задає світову точку правого хвату, додатковий лівий контакт, кут предмета, кути кистей та напрям згину. `rig.arms` зберігає базові довжини; `anatomyProjection` може описувати виправдане перспективне скорочення. У melee праву верхню кістку було невиправдано скорочено до 0.83589. У цьому проході для неї та передпліччя встановлено 1; нова точка хвату `[241,906]` досяжна без clamping. Розмір кисті не збільшувався.

`poseArt` містить окремі `image` (задня поверхня) та `frontImage` (передні пальці), `mesh`, `bind` та початкові `anchors`. Координати авторського малюнка відрізняються від поточних світових координат після зміни пози: перевірочні точки треба переводити через inverse bind, а не пересувати контрольну рамку навмання.

## Додавання іншого предмета

1. Створити окремий RGBA PNG та записати його `size`, `primary`, `support`, кут і масштаб у визначення класу. Не перемальовувати персонажа разом із предметом.
2. Для подібної рукоятки й відстані до цівки зберегти поточний варіант кисті. Налаштувати точки контакту й переконатися, що не відкриваються незавершені поверхні.
3. Для іншої товщини/кута рукоятки потрібен окремий художній варіант хвату в наявному `poseArt` та його реєстрація. Не розтягувати пальці й не заявляти сумісність будь-якої зброї з одним хватом. Поточний каталог Core має один варіант на клас; універсального автоматичного вибору хвату не реалізовано.
4. Перевірити передній і задній проходи, основний і додатковий контакти. Приховати предмет незалежним перемикачем. Поза, час і обидва проходи кистей мають лишитися незмінними.
5. Перевірити світлий/сірий/чорний/зелений фон, цикл, крайні фази та всі прямі переходи. Переглянути реальний рух.

У Lab є діагностичні розміри **85 / 100 / 115%**. `weaponPreviewScale` змінює лише малювання предмета навколо primary. Скелет і solver не перераховуються. Тому при 85/115% додатковий контакт rifle може розійтися — це демонстрація потреби іншого калібрування, не підтвердження сумісності. За 100% використовується звичайний предмет.

## Підготовка й власність пікселів

`tools/prepare-reference-arm-art.py` виконує джерельне розділення, а потім, коли доступні нові вихідні локальні правки, запускає `tools/prepare-independent-anatomy.py`. Останній відтворює обмежені домальовані задні поверхні, матування, покриття сіткою, перенесення краю стегна та нову melee-калібровку. Він не викликає генератор повторно. Локальні джерела й маски — `review/weapon-independent-anatomy/`.

372 вихідні пікселі краю стегна перенесено з лівих сегментів у `lower`; вихідні RGBA збережено. Чинний рендер читає виправлені `leftArmSkin` / `leftHandSkin`, а не історичні `hands/left-*-source.png`. Просте видалення смуги без відновлення `lower` було б помилкою. Історичні копії збережено незмінними.

Межі торса y=295 і y=760 закріплені до нерухомих голови та нижньої частини. Усередині грудної клітки збережено дихання 4000 мс. Обладнання torso використовує ту саму сітку з тими самими вузлами; окрема affine-матриця більше не розводить комір і пояс зі шкірою.

## Межа готовності

Нові локальні поверхні чоловічих кистей — художній результат для огляду, а не універсальна завершена анатомія для будь-якої рукоятки. Потрібне візуальне приймання переходу нового лівого зап’ястя rifle, короткого trigger-пальця pistol та відмінностей фактури. Обидві статі мають активні бойові poseArt у Lab. Поточні похідні руки вибираються через `{gender}-preview.json.poseArtSurfaces`, доповнення покриття — `poseMeshExtensions`, а чоловічі очищені базові шари — `runtimeSurfaces`. Оригінали захищені. Це лабораторне приймання, не production-інтеграція чи автоматична сертифікація всього гардероба.

## Розслаблена поза з ножем і діагностичний одяг

`relaxed-melee.mjs` обчислює незмінну нейтральну авторську позу за її параметрами, а фазовий рух задає кутами upper ±0.035°, fore ±0.12°, hand ±1.6°. Немає IK-компенсації нерухомого ножа. Матриця кисті залишається джерелом матриці предмета; CSS-масштаб не змінює амплітуду.

`bindEquipment.poseSources` приймає окремі `{image, frontImage}` для авторських поз. Їхнє полотно повинно точно відповідати `poseArt.mesh.bounds`; вони використовують ту саму corrective-сітку й bind. Звичайний рукав у rest-space не вважається перевіреним для іншої художньої форми руки. Діагностичні сітки готуються `tools/prepare-foundation-diagnostics.py`. Колір шару тіла в Lab — технічний hue-probe, а не реалізація фінальних тонів шкіри. Для кожного нового предмета потрібен власний перевірений primary/support і відповідний хват; 85/115% явно непідтримувані діагностичні варіанти.

Відтворено масштабний шов при CSS320/DPR1: альфа шиї 150 замість253; при391.5 — альфа талії229 замість253. Виправлення: усі частини спочатку складаються на спільному нативному941×1672 Canvas; на екран масштабується одна готова прозора композиція. Фон додається останнім на вихідному Canvas. Це усуває взаємне згладжування суміжних вирізів, не підфарбовуючи щілину.

## Foundation cleanup: композиція та ніж

У melee `relaxed-melee.mjs` додає рух до авторських кутів вперед: upper ±0,035°, fore ±0,12°, кисть ±1,6°. Зброя успадковує матрицю кисті; inverse solve нерухомого ножа не виконується. Період лишається 4000 мс, перемикання — instant cut.

`poseArtCompleteSurfaces` містить завершену поверхню руки. Вона рендериться один раз; окремий предмет із передніми пальцями складається через `source-atop` тільки в межах альфи предмета. Це зберігає край шкіри при приховуванні предмета. Передній шар обмежений дистальною зоною від зап’ястя, а не горизонтальною межею всього передпліччя.

Персонаж спочатку складається у 941×1672, потім масштабується одним проходом. Це усуває шви незалежно масштабованих частин біля шиї/талії. Торс і діагностичний одяг використовують одну сітку з фіксованими межами y295/y760. `runtimeSurfaces` чоловіка вказує на похідні копії з очищеним слабким alpha-шумом; затверджена база залишається незмінною.

Діагностичний одяг із `assets/diagnostics` — контроль UV/масок, а не підтвердження готовності реального гардероба. Варіанти зброї 85/115% — діагностика, для них потрібне окреме калібрування хватів. Нові записи `.avframes` зберігають усі RGBA-байти 241 логічного кадру; WebP-прев’ю зменшені до 400×711 і 20 кадрів/с. Частота логічної вибірки не є вимірюванням реального FPS.

## Requested corrections: source ownership and item preview

`torso-space.mjs` defines the pinned breathing coordinate shared by the torso,
arm-root skin vertices and corrective art. Internal 2 px source-owned reserves
at Y=300–530 close partition seams; the exterior silhouette is not dilated.
Female lateral bra pixels remain torso-owned. At the exact rest frame the
renderer reuses the original runtime surface and the same masked head texture
as animated poses, preserving neutral RGBA and head fringe consistency.

`poseCalibration` is a runtime clone override, not a mutation of protected rig
JSON: male melee target `[241,920]`; female `[230,895]`, projections `[1,1]`.
The base bone lengths, forward knife motion, 4000 ms cycle and instant cut remain.

`equipment-weapons.json` registers existing inventory IDs, a shared PNG, type,
pose and per-gender primary/support/scale/angle/stock profiles.
`await engine.equipWeaponItem(id)` updates the renderer; `null` removes the item
and selects idle. This API itself never writes saves or grants inventory.
The approved visible-source derivatives are explicitly `PARTIAL`: concealed
handle/fore-end material is unavailable, so no full reconstruction is claimed.

The opt-in `index.html?avatarCore=1` adapter reads the existing Paper Doll state
and inventory flow. Central scene and wardrobe share the selected item ID;
there are no new save keys, item IDs, statistics or prices. The immutable game
catalog is unchanged; visual metadata stays in the separate Core catalog.
Unprepared real garments keep the existing renderer and a blocked marker,
rather than disappearing or being advertised as correctly rigged sleeves.
This mode is for review, not approved production integration.

See [the 22-issue report](../review/avatar-requested-corrections/README.md).

## Вибірковий review після 5532a93

Робочий прохід: `review/avatar-selective-merge/README.md`; це кандидат, не production-затвердження. `184e392` та `766a71e` мають тотожний runtime. Нові arm/front/complete PNG у `assets/{male,female}/selective-merge/` зберігають alpha та distal wrist/grip RGBA; історичний male RGB комбінується з current повними поверхнями, female donor endpoints не відкочуються.

`relaxedMeleeAngles(arm,pose,breath,motion)` має сумісний необов’язковий профіль. Engine передає `posePreview.meleeMotion`: раніше опис із JSON не використовувався, а жорсткий hand swing давав близько 8 px на ножі при регуляторі 2 px. Профіль upper=.008°, fore=.025°, hand=.35° дає 1.981 / 1.825 px за hull усіх ненульових alpha-пікселів штатного предмета, 4000 ms. Для іншої моделі або діагностичного масштабу потрібне окреме вимірювання; саме значення регулятора не є доказом фізичного відхилення.

Lab обирає original-visible ID кнопками поз; legacy props доступні явно. Його ДО-панель тепер завантажує точні рендери 184e392 при 0 ms. Попередній підпис 184e392 над знімками c2822a7 був помилковим і виправлений без заміни історичних матеріалів.
