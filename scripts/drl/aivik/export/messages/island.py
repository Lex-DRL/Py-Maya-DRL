# coding=utf-8
__author__ = 'Lex Darlog (DRL)'

from drl_common import module_string as __ms
__mod = __ms(__name__)

TREES_TITLE = u'Группа Trees? %s' % __mod
TREES_MESSAGE = (
	u"Найдена группа, которая похожа на <_Trees>, "
	u"но она не точно соответствует названию родителя.\n"
	u"\n"
	u"(вероятно) Группа Trees: {0}\n"
	u"Родитель: {1}\n"
	u"\n"
	u"Обработать её как группу Trees?"
)
TREES_YES_TIP = u'Почистить потомков этой группы как деревья'
TREES_NO_TIP = u'Пропустить группу'
TREES_YES_ALL_TIP = (
	u"Для всех остальных частичных совпадений в течение этой чистки — "
	u"не отображать больше это диалоговое окно и чистить объект как дерево."
	u"Даже если имя совпадает лишь частично."
)

# ---------------------------------------------------------

COLOR_SETS_TITLE = u"Сохранить colorSet? %s" % __mod
COLOR_SETS_MESSAGE = (
	u"Похоже, что следующему объекту нужно сохранить Color Set. "
	u"Но его название неточно совпадает с ожидаемым\n"
	u"\n"
	u"Объект: {0}\n"
	u"Похоже, что это: {1}\n"
	u"\n"
	u"Сохранить его VertexColor'ы?"
)
COLOR_SETS_YES_TIP = u"Сохранить VertexColor'ы"
COLOR_SETS_NO_TIP = u"Удалить VertexColor'ы"
COLOR_SETS_CANCEL = u"Прервать экспорт"
COLOR_SETS_CANCEL_TIP = (
	u'Прервать процесс экспорта. '
	u'Сцена может быть уже частично "поломана" '
	u'(если какие-то чистки уже произошли)'
)
