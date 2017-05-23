# coding=utf-8
__author__ = 'DRL'

from drl_common import module_string as __ms
__mod = __ms(__name__)

DIR_TITLE = u'Выбор папки для экспорта %s' % __mod
DIR_YES = u'Выгрузить в эту папку'
DIR_NO = u'Отмена'

# ---------------------------------------------------------

CANCEL_TITLE = u'Папка не выбрана %s' % __mod
CANCEL_MESSAGE = u"""
Папка не выбрана.

Прекратить процесс экспорта?
""".strip('\n')
CANCEL_YES = u'Да (прервать экспорт)'
CANCEL_YES_TIP = u'FBX-файлы не будут созданы'
CANCEL_NO = u'Нет'
CANCEL_NO_TIP = u'Вернуться к окну, в котором можно выбрать папку'