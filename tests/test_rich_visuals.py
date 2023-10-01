from rich import print
from rich.layout import Layout
from rich.panel import Panel

from llmagic.block import Block, TextBlock

grandparent_block = Block(name="grandparent")
parent_block = Block(name="parent")
child_a = TextBlock(
    name="child a",
    text="""The Cuban Revolution (Spanish: Revolución cubana) was a military and political effort to overthrow the government of Cuba between 1953 and 1959. It began after the 1952 Cuban coup d'état which placed Fulgencio Batista as head of state and the failed mass strike in opposition that followed. After failing to contest Batista in court, Fidel Castro organized an armed attack on the Cuban military's Moncada Barracks on July 26, 1953. The rebels were arrested and while in prison formed the 26th of July Movement. After gaining amnesty the M-26-7 rebels organized an expedition from Mexico on the Granma yacht to invade Cuba. In the following years the M-26-7 rebel army would slowly defeat the Cuban army in the countryside, while its urban wing would engage in sabotage and rebel army recruitment. Over time the originally critical and ambivalent Popular Socialist Party would come to support the 26th of July Movement in late 1958. By the time the rebels were to oust Batista the revolution was being driven by the Popular Socialist Party, 26th of July Movement, and the Revolutionary Directorate of March 13.[8]
The rebels finally ousted Batista on 1 January 1959, replacing his government. 26 July 1953 is celebrated in Cuba as Día de la Revolución (from Spanish: "Day of the Revolution"). The 26th of July Movement later reformed along Marxist–Leninist lines, becoming the Communist Party of Cuba in October 1965.[9]
The Cuban Revolution had powerful domestic and international repercussions. In particular, it transformed Cuba–United States relations, although efforts to improve diplomatic relations, such as the Cuban thaw, gained momentum during the 2010s.[10][11][12][13] In the immediate aftermath of the revolution, Castro's government began a program of nationalization, centralization of the press and political consolidation that transformed Cuba's economy and civil society.[14][15] The revolution also heralded an era of Cuban intervention in foreign conflicts in Africa, Latin America, Southeast Asia, and the Middle East.[16][17][18][19] Several rebellions occurred in the six years following 1959, mainly in the Escambray Mountains, which were suppressed by the revolutionary government.[20][21][22][23]""",
)
child_b = TextBlock(name="child b", text="This is another block")
parent_block = parent_block + child_a + child_b
grandparent_block += parent_block
print(grandparent_block.rich_text)
