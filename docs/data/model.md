# Логическая модель данных и нормализация

Модель предназначена для проектирования; она не является миграцией или утверждением о готовой реализации. Служебные таблицы Identity, токены и индексы будут уточняться при физическом проектировании.

## User - Пользователь
id UUID PK; email varchar(254) UNIQUE; password_hash text; display_name varchar(80); role enum(user,admin); is_blocked boolean; created_at timestamptz

У каждого пользователя одна бизнес-роль. В реализации допускается отображение на таблицы ASP.NET Core Identity.

## Category - Категория
id integer PK; name varchar(80) UNIQUE; slug varchar(80) UNIQUE; sort_order integer

Название и порядок хранятся один раз в справочнике.

## Dormitory - Общежитие
id integer PK; name varchar(80) UNIQUE; address varchar(250)

Ссылка на карту вычисляется из адреса; адрес не дублируется в объявлении.

## Listing - Объявление
id integer PK; owner_id UUID FK User; category_id integer FK Category; dormitory_id integer NULL FK Dormitory; custom_location varchar(250) NULL; title varchar(120); description text; price numeric(12,2); condition enum; contact_type enum; contact_value varchar(250); status enum; created_at, updated_at timestamptz; published_at, sold_at timestamptz NULL; moderated_by_id UUID NULL FK User; moderated_at timestamptz NULL; rejection_reason text NULL; deleted_at timestamptz NULL; version bigint

Цена ≥ 0; место: ровно одно из dormitory_id и custom_location. Модератор отличается от владельца по роли связи. Хранится последнее решение, не полный журнал.

## Photo - Фотография
id integer PK; listing_id integer FK Listing; storage_key varchar(250) UNIQUE; content_type varchar(40); sort_order integer; UNIQUE(listing_id, sort_order)

Одна запись на файл; 1-5 фото проверяются сервисом в транзакции перед подачей объявления.

## Favorite - Избранное
user_id UUID FK User; listing_id integer FK Listing; created_at timestamptz; PK(user_id, listing_id)

Связь многие-ко-многим без повторов.

## Report - Жалоба
id integer PK; listing_id integer FK Listing; reporter_id UUID FK User; reason enum; details text NULL; status enum(open,resolved); created_at timestamptz; resolved_by_id UUID NULL FK User; resolved_at timestamptz NULL; resolution_action enum NULL; resolution_comment text NULL; version bigint

Для resolved обязательны исполнитель, время и действие. Независимая сущность; на объявление может быть несколько жалоб.

## Notification - Уведомление
id integer PK; user_id UUID FK User; listing_id integer NULL FK Listing; type enum; text text; created_at timestamptz; read_at timestamptz NULL

Текст - самостоятельный снимок события, а не копия изменяемого описания объявления.

## Связи и ограничения
- User 1 → 0..* Listing как владелец; у объявления ровно один владелец.
- Category 1 → 0..* Listing; у объявления ровно одна категория.
- Dormitory 1 → 0..* Listing; у объявления 0..1 общежитие.
- Listing 1 → 1..5 Photo в поданном объявлении; ограничение числа строк контролирует сервис.
- User и Listing связаны M:N через Favorite, по 0..* с каждой стороны.
- Listing 1 → 0..* Report; каждая жалоба имеет одного автора и 0..1 администратора-исполнителя.
- User 1 → 0..* Notification; у уведомления 0..1 связанное объявление.
- У Listing 0..1 последний модератор, у User 0..* проверенных объявлений.

Физические удаления пользователей и объявлений не входят в обычный интерфейс; применяется блокировка/скрытие. Внешние ключи ссылаются на сохраненные записи, каскадное удаление истории жалоб не применяется. Индексы планируются на Listing(status, created_at), category_id, dormitory_id, owner_id и на внешние ключи очередей. Совпавшая версия обязательна для обновления Listing и Report; конфликт возвращается клиенту.

## Обоснование 3НФ
1НФ: атрибуты атомарны, фото и избранное представлены отдельными строками, списков идентификаторов в полях нет.
2НФ: у сущностей с простым ключом каждый неключевой атрибут зависит от полного ключа. В Favorite единственный неключевой атрибут created_at характеризует всю пару (user_id, listing_id), а не одного участника пары.
3НФ: для каждой сущности определяющими ключами являются ее PK и явно указанные UNIQUE-кандидаты. Названия категорий, адрес общежития и имя владельца вынесены в отдельные сущности; в Listing находятся ссылки, а не копии этих атрибутов. Контакт объявления является отдельным фактом конкретного предложения и может отличаться от контактов других объявлений владельца. Notification.text фиксирует событие. Не хранится вычисляемый флаг «бесплатно» - это price = 0. При этих бизнес-зависимостях транзитивные зависимости неключевых атрибутов исключены.

Перечисления состояния, статуса, типа контакта и причины жалобы - атомарные домены без дополнительных описательных столбцов; при появлении переводов или изменяемых свойств их следует вынести в справочники.

ER-диаграмма (см. редактируемую схему в этой папке) показывает ключи и кардинальности. Полный словарь атрибутов приведен выше, редактируемая ER-модель - [er_diagram.puml](er_diagram.puml).
