/* Floor-ten staff conversations. This view never writes saves or pays rewards.
   The quest adapter supplies the only state-changing callback. */
(function (root) {
    'use strict';

    const staff = {nurse: 'Клара', doctor: 'Дежурный врач'};

    const conversations = {
        k1: {
            giver: 'nurse',
            title: 'Комплект для процедурной',
            offer: 'Сможешь сверить контейнеры в процедурной? На пост нужен только тот комплект, который указан в заявке.',
            active: 'Ты уже в деле. Если не уверен в контейнере, сверь его с заявкой ещё раз.',
            ready: 'Есть бирка? Давай посмотрим, какой контейнер ты нашёл.',
            complete: 'Маркировка и партия сошлись, пломба цела. Этот комплект можно передавать на пост.',
            accept: 'Проверю комплект',
            claim: 'Передать бирку',
            motive: 'На полке похожие контейнеры. Если взять чужую партию, пост будет ждать свой комплект зря.',
            details: 'В процедурной осмотри контейнеры, прочитай заявку и выбери подходящий. Принеси бирку проверенного комплекта.',
            hint: 'Одной знакомой маркировки мало. Смотри на партию и целость пломбы.'
        },
        k2: {
            giver: 'nurse',
            title: 'Чистое бельё для палаты 406',
            offer: 'В четыреста шестой нужно застелить кровать. Возьмёшь в бельевой чистую простыню и наволочку?',
            active: 'Когда кровать будет готова, принеси квитанцию. Если что-то помешает, разберёмся по заявке.',
            ready: 'Кровать готова? Тогда отдай квитанцию, я отмечу смену белья.',
            complete: 'Спасибо. Бельё на месте, запись в журнале есть.',
            accept: 'Возьмусь за бельё',
            claim: 'Передать квитанцию',
            motive: 'В четыреста шестой ждут чистое место. Лучше переменить обе вещи за один раз.',
            details: 'Собери комплект по заявке из бельевой. Если нужной вещи не хватает, запиши недостачу и подойди ко мне.',
            hint: 'На упаковках смотри и на маркировку, и на размер. В палате рабочий лист покажет, какую вещь можно положить.'
        },
        k3: {
            giver: 'nurse',
            title: 'Записи процедурной',
            offer: 'Поможешь сверить записи из процедурной? В копии есть строка, которой я не доверяю.',
            active: 'Я оставила документы в процедурной. Отметь то, что можешь подтвердить по листам.',
            ready: 'Покажи результаты сверки. Что именно подтверждают записи?',
            complete: 'Принято. Оставлю подтверждённые сведения, остальное проверю отдельно.',
            accept: 'Сверю записи',
            claim: 'Передать лист сверки',
            motive: 'Если копию перескажут дальше, ошибка станет похожа на достоверную запись.',
            details: 'Сверь поля в выданных документах. Смотри, к чему относится каждое время и что действительно написано в строке исполнителя.',
            hint: 'Неразборчивая строка не подтверждает имя. Плановое время и время выполнения тоже могут быть разными полями.'
        },
        d1: {
            giver: 'doctor',
            title: 'Вызовы из палат 407 и 408',
            offer: 'Мне нужны два акта о вызовах из палат 407 и 408. Проверьте, что происходит у кнопки и отвечает ли пост.',
            active: 'Запишите состояние каждой линии отдельно. Сначала наблюдение, потом вывод.',
            ready: 'Оба акта готовы. Передайте их, чтобы я закрыл проверку.',
            complete: 'Результаты приняты. Состояние каждой линии внесено в журнал.',
            accept: 'Начать проверку',
            claim: 'Передать акты',
            motive: 'Горящий индикатор показывает сигнал на узле. Ответ поста нужно подтвердить отдельно.',
            details: 'Осмотрите подключение и выполните пробный вызов в каждой палате. Если обнаружите неполадку, действуйте по своему рабочему листу.',
            hint: 'Запишите состояние разъёма, индикатора и ответ. Если назначено обслуживание, сверьте маркировку узла и адрес для контрольного вызова.'
        },
        d2: {
            giver: 'doctor',
            title: 'Журнал обхода',
            offer: 'Листы обхода перемешали. Разложите их в том порядке, который можно подтвердить записями.',
            active: 'Журнал здесь. Вернитесь к листам, если последовательность ещё не подтверждена.',
            ready: 'Листы собраны? Покажите порядок обхода.',
            complete: 'Порядок принят. Неразборчивое время оставим неустановленным.',
            accept: 'Разобрать журнал',
            claim: 'Передать журнал',
            motive: 'Нам нужен порядок событий, чтобы понять, кто и когда мог зафиксировать наблюдение.',
            details: 'Расположите листы по событиям. Если время на одном листе не читается, используйте только подтверждённые сведения.',
            hint: 'Переверните лист с неразборчивым временем. Отметка до или после другого события может заменить точное время.'
        },
        d3: {
            giver: 'doctor',
            title: 'Повторное наблюдение',
            offer: 'Нужны две записи одного наблюдения. Запишите первое показание и повторите ту же проверку после смены состояния.',
            active: 'Сохраняйте предмет и способ проверки. Сравнение имеет смысл, если в обеих карточках речь об одном и том же.',
            ready: 'Принесите обе записи. Если всё совпало, это тоже результат.',
            complete: 'Карточку принял. Зафиксируем наблюдение, причину пока оставим открытой.',
            accept: 'Начать наблюдение',
            claim: 'Передать карточку',
            motive: 'По одной записи нельзя понять, что именно изменилось и изменилось ли что-нибудь.',
            details: 'Сохраните первую запись в состоянии «Пациент» и повторите ту же проверку после входа в Трип. Сопоставьте факты в двух карточках.',
            hint: 'Записывайте только увиденное. При совпадении отметьте совпадение. Если отклика не было, так и запишите.'
        }
    };

    const topics = [['motive', 'Зачем?'], ['details', 'Что делать?'], ['hint', 'Подсказка']];
    const phases = ['offer', 'active', 'ready', 'complete'];
    let dialog;
    let current;

    function element(tag, className, text) {
        const result = document.createElement(tag);
        if (className) result.className = className;
        if (text) result.textContent = text;
        return result;
    }

    function control(text, onClick) {
        const button = element('button', '', text);
        button.type = 'button';
        button.addEventListener('click', onClick);
        return button;
    }

    function outcomeText(conversation) {
        const {id, outcome} = conversation;
        if (!outcome) return '';
        if (typeof outcome === 'string') return outcome;
        if (id === 'k2' && outcome.method === 'assistance') {
            return 'Край мы придержали вместе. Теперь простыня лежит ровно.';
        }
        if (id === 'k2' && outcome.method === 'window') {
            return 'После того как прикрыли окно, простыню больше не поднимало.';
        }
        return typeof outcome.result === 'string' ? outcome.result : '';
    }

    function topicText(conversation, key) {
        const {id, revision} = conversation;
        if (id === 'd1' && revision >= 5 && key === 'details') {
            return 'Проверьте первый узел на месте. Если нужен техник, сверим с ним запись обслуживания там же. Контрольный вызов сделайте до перехода в другую палату.';
        }
        if (id === 'k3' && revision < 3 && key === 'hint') {
            return 'Сверь время, палату, подпись и комплект. Пустая строка отличается от подписанной.';
        }
        if (id === 'd2' && revision < 3 && key === 'hint') {
            return 'Сначала прочитайте время на каждом листе. Более ранняя запись должна идти раньше в журнале.';
        }
        if (id === 'd3' && key === 'details' && revision >= 4) {
            return 'Сначала выберите доступный предмет на рабочем листе. Запишите исходное наблюдение в состоянии «Пациент», затем повторите ту же проверку в Трипе.';
        }
        if (id === 'd3' && key === 'hint' && revision < 4) {
            return 'Сопоставьте время обхода, маршрут и отметку на табличке. Если все три поля совпали, не придумывайте изменения.';
        }
        return conversations[id][key];
    }

    function close(reason = 'programmatic') {
        if (!current) return;
        const departing = current;
        current = null;
        dialog.close();
        departing.onClose?.(reason);
        const target = departing.restoreFocus?.() || departing.anchor;
        if (!current && target?.isConnected && target.getClientRects().length) {
            target.focus({preventScroll: true});
        }
    }

    function ensureDialog() {
        if (dialog) return;
        dialog = element('dialog', 'quest-staff-dialogue');
        dialog.id = 'quest-staff-dialogue';
        dialog.setAttribute('role', 'dialog');
        dialog.setAttribute('aria-modal', 'true');
        dialog.setAttribute('aria-labelledby', 'quest-dialogue-character quest-dialogue-title');
        dialog.addEventListener('cancel', event => {
            event.preventDefault();
            close('escape');
        });
        dialog.addEventListener('keydown', event => {
            if (event.key === 'Tab') event.stopPropagation();
            if (event.key === 'Escape') {
                event.stopPropagation();
                event.preventDefault();
                close('escape');
            }
        });
        document.body.append(dialog);
    }

    function confirm(conversation, primary, error) {
        if (current !== conversation || conversation.confirming) return;
        conversation.confirming = true;
        primary.disabled = true;
        error.hidden = true;
        let result;
        try {
            result = conversation.onConfirm?.();
        } catch (error) {
            console.error(error);
        } finally {
            conversation.confirming = false;
        }
        if (current !== conversation) return;
        if (result !== true && result?.ok !== true) {
            primary.disabled = false;
            error.textContent = result?.message || 'Действие не подтверждено. Проверьте сохранение и попробуйте снова.';
            error.hidden = false;
            primary.focus({preventScroll: true});
            error.scrollIntoView({block: 'nearest'});
            return;
        }
        conversation.phase = conversation.phase === 'offer' ? 'active' : 'complete';
        conversation.stage = conversation.getStage?.() ?? conversation.stage;
        conversation.outcome = conversation.getOutcome?.() ?? conversation.outcome;
        render(conversation);
    }

    function render(conversation) {
        const {id, phase, stage, outcome, revision} = conversation;
        const script = conversations[id];

        dialog.dataset.job = id;
        dialog.dataset.phase = phase;
        const paper = element('article', 'quest-dialogue-paper document-paper');
        const head = element('header', 'quest-dialogue-head');
        const portraitPath = root.PalataFloorArt?.resolve(script.giver, 'patient').portrait;
        if (portraitPath) {
            const portrait = element('img', 'quest-dialogue-portrait');
            portrait.src = portraitPath;
            portrait.alt = '';
            portrait.draggable = false;
            head.append(portrait);
        }
        const titles = element('div', 'quest-dialogue-titles');
        const character = element('p', 'quest-dialogue-character', staff[script.giver]);
        character.id = 'quest-dialogue-character';
        const heading = element('h2', '', script.title);
        heading.id = 'quest-dialogue-title';
        heading.tabIndex = -1;
        titles.append(character, heading);
        head.append(titles);

        const body = element('div', 'quest-dialogue-body');
        const line = id === 'd2' && revision < 3 && phase === 'complete'
            ? 'Порядок принят. Листы снова на своих местах.' : script[phase];
        body.append(element('p', 'quest-dialogue-line', line));
        const stageText = typeof stage === 'string' ? stage : stage?.text;
        if (phase === 'active' && stageText) {
            body.append(element('p', 'quest-dialogue-guidance', stageText));
        }
        const result = outcomeText(conversation);
        if (result && ['ready', 'complete'].includes(phase)) {
            body.append(element('p', 'quest-dialogue-guidance', result));
        }
        if (phase === 'complete' && typeof outcome?.reward === 'string' && !result.includes(outcome.reward)) {
            body.append(element('p', 'quest-dialogue-payout', outcome.reward));
        }

        if (phase !== 'complete') {
            const nav = element('nav', 'quest-dialogue-topics');
            nav.setAttribute('aria-label', 'Вопросы');
            const reply = element('p', 'quest-dialogue-reply');
            reply.id = 'quest-dialogue-reply';
            reply.setAttribute('role', 'status');
            for (const [key, title] of topics) {
                const topic = control(title, () => {
                    const expanded = topic.getAttribute('aria-expanded') === 'true';
                    for (const other of nav.children) other.setAttribute('aria-expanded', 'false');
                    topic.setAttribute('aria-expanded', String(!expanded));
                    reply.textContent = expanded ? '' : topicText(conversation, key);
                });
                topic.dataset.dialogueTopic = key;
                topic.setAttribute('aria-controls', reply.id);
                topic.setAttribute('aria-expanded', 'false');
                nav.append(topic);
            }
            body.append(nav, reply);
        }

        const error = element('p', 'quest-dialogue-error');
        error.setAttribute('role', 'alert');
        error.hidden = true;
        body.append(error);

        const footer = element('footer', 'quest-dialogue-actions');
        if (phase === 'offer' || phase === 'ready') {
            const primary = control(phase === 'offer' ? script.accept : script.claim, () => confirm(conversation, primary, error));
            primary.dataset.dialogueConfirm = phase;
            primary.className = 'quest-dialogue-primary';
            footer.append(primary);
        }
        const finish = phase === 'complete';
        const cancel = control(finish ? 'Закрыть' : 'Вернусь позже', () => close(finish ? 'done' : 'defer'));
        cancel.dataset.dialogueClose = '';
        footer.append(cancel);
        paper.append(head, body, footer);
        dialog.replaceChildren(paper);
        if (!dialog.open) dialog.showModal();
        heading.focus({preventScroll: true});
    }

    function open(options) {
        if (!options || !Object.hasOwn(conversations, options.id) || !phases.includes(options.phase)) return false;
        ensureDialog();
        current = {...options, anchor: options.anchor || document.activeElement};
        render(current);
        return true;
    }

    root.PalataQuestDialogues = Object.freeze({open, close});
})(globalThis);
