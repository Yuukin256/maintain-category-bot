from datetime import date
from queue import Queue

import pywikibot
from dateutil.relativedelta import relativedelta
from pywikibot import editor as editarticle
from pywikibot.tools.formatter import color_format


class BaseCategory():
    """
    基幹のカテゴリ

    Returns:
        str: カテゴリの名前
    """
    def __init__(self, site: pywikibot.Site, title: str, month_parent=None, year_parent=None, seperater='/', toc=None):
        """
        Args:
            site (pywikibot.Site): サイト
            title (str): カテゴリの名前
            month_parent ([type], optional): 月ごとに分類するカテゴリの親カテゴリ (Defaults to None.)
            year_parent ([type], optional): 年ごとに分類するカテゴリの親カテゴリ (Defaults to None.)
            seperater (str, optional): カテゴリ名のタイトルと年月の区切り (Defaults to '/'.)
            toc ([type], optional): 目次 (Defaults to None.)
        """
        self.site = site
        self.title = title
        self.name_date_sep = seperater

        self.year_cats_parent = [title + '|{year}']
        if year_parent:
            self.year_cats_parent.append(year_parent)
        self.month_cats_parent = [title + seperater + '{year}年|{year}{zfill_month}']
        if month_parent:
            self.month_cats_parent.append(month_parent)

    def __repr__(self):
        return self.title


class YearCategory(pywikibot.Category):
    def __init__(self, base: BaseCategory, year: int):
        self.basecat = base
        self.year = year
        self.newtext = ''
        self.parent_cats = [p.format(year=year) for p in base.year_cats_parent]

        super(YearCategory, self).__init__(base.site, f'{base.title}{base.name_date_sep}{year}年')

    def get_newtext(self) -> str:
        if not self.newtext:
            self.make_newtext()
        return self.newtext

    def make_newtext(self) -> None:
        text = '{{Hiddencat}}\n'
        text += f'{{{{前後年月カテゴリ|前年={self.year - 2}年|前月={self.year - 1}年|後月={self.year + 1}年|後年={self.year + 2}年}}}}\n'
        for c in self.parent_cats:
            text += f'[[{c}]]\n'

        self.newtext = text


class MonthCategory(pywikibot.Category):
    def __init__(self, base: BaseCategory, year: int, month: int):
        self.basecat = base
        self.date = date(year, month, 1)
        self.newtext = ''
        self.parent_cats = [p.format(year=year, month=month, zfill_month=str(month).zfill(2))
                            for p in base.month_cats_parent]

        super(MonthCategory, self).__init__(base.site, f'{base.title}{base.name_date_sep}{year}年{month}月')

    def get_newtext(self) -> str:
        if not self.newtext:
            self.make_newtext()
        return self.newtext

    def make_newtext(self) -> None:
        text = '{{Hiddencat}}\n'
        prev_year = self.date - relativedelta(years=1, months=1)
        prev_month = self.date - relativedelta(months=1)
        next_month = self.date + relativedelta(months=1)
        next_year = self.date + relativedelta(years=1, months=1)
        text += f'{{{{前後年月カテゴリ|前年={prev_year.year}年|前月={prev_month.year}年{prev_month.month}月'\
            f'|当年={self.date.year}年|後月={next_month.year}年{next_month.month}月|後年={next_year.year}年}}}}\n'
        for c in self.parent_cats:
            text += f'[[{c}]]\n'

        self.newtext = text


class MaintainCategoryRobot(pywikibot.Bot):
    def __init__(self, site):
        super(MaintainCategoryRobot, self).__init__(site)

        self.changed_pages = 0
        self._pending_processed_titles = Queue()

    def _async_callback(self, page, err):
        if not isinstance(err, Exception):
            self.changed_pages += 1
            self._pending_processed_titles.put((page.title(as_link=True), True))
        else:
            self._pending_processed_titles.put((page.title(as_link=True), False))

    def make_list(self) -> None:
        base_categories = [BaseCategory(self.site, 'Category:Wikifyが必要な項目'),
                           BaseCategory(self.site, 'Category:外部リンクがリンク切れになっている記事'),
                           BaseCategory(self.site, 'Category:雑多な内容を箇条書きした節のある記事', seperater=' - '),
                           BaseCategory(self.site, 'Category:出典を必要とする記事',
                                        toc='{{CategoryTOC3\n||人|タグに没年記入ありの人物記事|\n||音|音楽作品に関する記事|\n}}'),
                           BaseCategory(self.site, 'Category:出典を必要とする記述のある記事',
                                        'Category:出典を必要とする記事/{year}年{month}月|***',
                                        'Category:出典を必要とする記事|****',
                                        toc='{{CategoryTOC3}}'),
                           BaseCategory(self.site, 'Category:出典を必要とする存命人物記事',
                                        'Category:出典を必要とする記事/{year}年{month}月|**そんめい',
                                        'Category:出典を必要とする記事|***そんめい',
                                        toc='{{CategoryTOC3}}'),
                           BaseCategory(self.site, 'Category:出典皆無な存命人物記事',
                                        'Category:出典を必要とする存命人物記事/{year}年{month}月|*',
                                        'Category:出典を必要とする存命人物記事/{year}年|*',
                                        toc='{{CategoryTOC3}}'),
                           BaseCategory(self.site, 'Category:独自研究の除去が必要な記事',
                                        'Category:出典を必要とする記事/{year}年{month}月|*とくしけんきゆう'),
                           BaseCategory(self.site, 'Category:特筆性の基準を満たしていないおそれのある記事',
                                        'Category:出典を必要とする記事/{year}年{month}月|*とくひつせい')]

        basecat = pywikibot.bot.input_list_choice('カテゴリを選択', base_categories)
        pywikibot.output(f'「{basecat}」を選択')

        year = 0
        while True:
            year = int(pywikibot.input('年を入力'))
            if year > date.today().year or year < 2010:
                pywikibot.output('有効な年を入力してください')
            else:
                break

        self.parent = YearCategory(basecat, year)
        self.children = [MonthCategory(basecat, year, m) for m in range(1, 13)]

    def run(self) -> None:
        self._post(self.parent)
        for page in self.children:
            self._post(page)

        pywikibot.output(f'{self.changed_pages} ページ編集しました')
        pywikibot.output(f'{self.parent.title(as_link=True)} 関連の整備が完了しました')

    def _post(self, page):
        original_text = page.text
        new_text = page.get_newtext()

        while True:
            pywikibot.output(color_format(
                '\n\n>>> {lightpurple}{0}{default} <<<', page.title()))
            pywikibot.showDiff(original_text, new_text)
            choice = pywikibot.input_choice('この変更を投稿しますか', [('はい', 'y'), ('いいえ', 'n'), ('エディタで編集する', 'e')])
            if choice == 'n':
                return False
            if choice == 'e':
                editor = editarticle.TextEditor()
                as_edited = editor.edit(new_text)
                if as_edited:
                    new_text = as_edited
                continue
            if choice == 'y':
                page.text = new_text
                page.save(
                    'Botによる: [[User:YuukinBot#作業内容2|カテゴリの整備]]',
                    asynchronous=True,
                    callback=self._async_callback,
                    quiet=True)
            while not self._pending_processed_titles.empty():
                proc_title, res = self._pending_processed_titles.get()
                pywikibot.output('{0}{1}'.format(proc_title, 'が投稿されました' if res else 'は投稿されませんでした'))


def main():
    site = pywikibot.Site(user='YuukinBot')
    site.login()

    while True:
        bot = MaintainCategoryRobot(site)
        bot.make_list()
        bot.run()

        choice = pywikibot.input_choice('他のカテゴリで続行しますか', [('はい', 'y'), ('いいえ', 'n')])
        if choice == 'y':
            continue
        if choice == 'n':
            break


if __name__ == "__main__":
    main()
