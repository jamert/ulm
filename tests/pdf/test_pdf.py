import pytest

from unstructured.partition.text import element_from_text

from ulm.pdf import needs_merge

p1 = "Staying with repair as practice allows for a more careful consideration of how human labor works in and through infrastructure. Building on theorizations of repair and maintenance as improvisational and adaptive labor, driven by human ingenuity (Graham and Thrift, 2007), I push these arguments forward by considering how that work is learned, carried out, and how it emerges from the specific geohistorical context of the Mexico City’s networked water system. Namely, I show how patchwork is a result of structural austerity, widespread (yet unequal and uneven) infrastructural decay, and of the changing flows of urban water and urban soil. Patchwork is an improvisational logic that enables the city to"
footer_text = "De Coss-Corzo"
page_number = "3"
p2 = "endure not by returning “to a former, officially authorized state” (Barnes, 2017: 154), but by adapting the grid to changing conditions and breakdowns, both foreseen and unforeseen, in ways that exceed and challenge official narratives, rules, and practices. In staying with the question of repair, patchwork also stays with the moment of rupture, distinguishing between preventative logics of maintenance that seek to act before breakdown, and those of adaptation and improvisation that emerge as infrastructure fails."
p3 = "The observations discussed here were gathered through a one-year ethnography at SACMEX. I focus particularly on the participant observation carried out with four SACMEX repair teams, each composed of 5–7 workers, with whom I worked full-time the Lerma System shifts two or three times per week. Two teams were part of Subdirectorate, based in Lerma, a periurban area in the state of Mexico, which supplies 12% of Mexico City’s water (SACMEX, 2018). The other two were part of the Mexico Citybased West Subdirectorate and worked in three Mexico City alcaldıas (boroughs) and one state of Mexico municipality—Huixquilucan. My role within these teams shifted as time went by. At the beginning I limited myself to observing, documenting, and carrying out informal interviews with workers. After two months, I started to help carrying tools and materials. Toward the middle of my fieldwork, I began engaging in minor repair and maintenance activities, in particular with one team in Lerma. My analysis of workers’ attitudes, resources, and practices when performing their labor comes from this embodied research experience as well. In all cases, their names have been changed, and locations have been made purposefully vague to ensure their anonymity."


@pytest.mark.parametrize(
    "e1, e2, expected",
    [
        pytest.param(p1, footer_text, False, id="ignore footer"),
        pytest.param(p1, page_number, False, id="ignore page number"),
        pytest.param(p1, p2, True, id="split paragraph"),
        pytest.param(p2, p3, False, id="separate paragraphs"),
    ],
)
def test_needs_merge(e1, e2, expected):
    assert needs_merge(element_from_text(e1), element_from_text(e2)) is expected
