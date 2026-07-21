"""Nielsen DMA reference — Datalogix DMA Code decoding.

Sources:
- https://ustvdb.com/seasons/2024-25/markets/ (2024-25 rank, TV households)
- https://www.emediamonitor.net/en/country-information/north-america/united-states-dmas/
- Nielsen 3-digit DMA codes (IAB Tech Lab reference)
"""

from __future__ import annotations

from dataclasses import dataclass

DMA_SEASON = "2024-25"

@dataclass(frozen=True)
class DmaMarket:
    code: str
    market_name: str
    slug: str | None = None
    rank_2024_25: int | None = None
    tv_homes_2024_25: int | None = None
    share_pct: str | None = None

    @property
    def tier(self) -> str:
        rank = self.rank_2024_25
        if rank is None:
            return "unranked"
        if rank <= 50:
            return "major"
        if rank <= 100:
            return "large"
        if rank <= 150:
            return "medium"
        return "small"

DMA_MARKETS: tuple[DmaMarket, ...] = (
    DmaMarket('500', 'Portland-Auburn, ME', 'portland-auburn', 78, 439030, '0.350%'),
    DmaMarket('501', 'New York', 'new-york', 1, 7494510, '5.972%'),
    DmaMarket('502', 'Binghamton', 'binghamton', 162, 132690, '0.106%'),
    DmaMarket('504', 'Philadelphia', 'philadelphia', 5, 3145920, '2.507%'),
    DmaMarket('505', 'Detroit', 'detroit', 14, 1940750, '1.547%'),
    DmaMarket('506', 'Boston (Manchester)', 'boston-manchester', 9, 2584460, '2.059%'),
    DmaMarket('507', 'Savannah', 'savannah', 84, 400190, '0.319%'),
    DmaMarket('508', 'Pittsburgh', 'pittsburgh', 27, 1167890, '0.931%'),
    DmaMarket('509', 'Ft. Wayne', 'fort-wayne', 110, 290520, '0.232%'),
    DmaMarket('510', 'Cleveland-Akron (Canton)', 'cleveland-akron-canton', 19, 1554340, '1.239%'),
    DmaMarket('511', 'Washington DC (Hagerstown)', 'washington-hagerstown', 8, 2630640, '2.096%'),
    DmaMarket('512', 'Baltimore', 'baltimore', 29, 1155000, '0.920%'),
    DmaMarket('513', 'Flint-Saginaw-Bay City', 'flint-saginaw-bay-city', 72, 458710, '0.366%'),
    DmaMarket('514', 'Erie', 'erie', 154, 151250, '0.121%'),
    DmaMarket('515', 'Cincinnati', 'cincinnati', 37, 958630, '0.764%'),
    DmaMarket('516', 'Norfolk-Portsmouth-Newport News', 'norfolk-portsmouth-newport-news', 44, 779970, '0.622%'),
    DmaMarket('517', 'Charlotte', 'charlotte', 21, 1382020, '1.101%'),
    DmaMarket('518', 'Greensboro-High Point-Winston Salem', 'greensboro-high-point-winston-salem', 46, 766980, '0.611%'),
    DmaMarket('519', 'Charleston, SC', 'charleston-sc', 85, 399960, '0.319%'),
    DmaMarket('520', 'Savannah', 'savannah', 84, 400190, '0.319%'),
    DmaMarket('521', 'Providence-New Bedford', 'providence-new-bedford', 52, 662810, '0.528%'),
    DmaMarket('522', 'Columbus, OH', 'columbus-oh', 35, 1018390, '0.812%'),
    DmaMarket('523', 'Burlington-Plattsburgh', 'burlington-plattsburgh', 93, 369840, '0.295%'),
    DmaMarket('524', 'Atlanta', 'atlanta', 7, 2758170, '2.198%'),
    DmaMarket('525', 'Madison', 'madison', 77, 443220, '0.353%'),
    DmaMarket('526', 'Albany, GA', 'albany-ga', 152, 153090, '0.122%'),
    DmaMarket('527', 'Indianapolis', 'indianapolis', 25, 1232210, '0.982%'),
    DmaMarket('528', 'Louisville', 'louisville', 49, 702310, '0.560%'),
    DmaMarket('529', 'Lexington', 'lexington', 63, 517660, '0.413%'),
    DmaMarket('530', 'Ft. Wayne', 'fort-wayne', 110, 290520, '0.232%'),
    DmaMarket('531', 'South Bend-Elkhart', 'south-bend-elkhart', 100, 331800, '0.264%'),
    DmaMarket('532', 'Albany-Schenectady-Troy', 'albany-schenectady-troy', 62, 575590, '0.459%'),
    DmaMarket('533', 'Hartford & New Haven', 'hartford-new-haven', 32, 1060910, '0.845%'),
    DmaMarket('534', 'Orlando-Daytona Beach-Melbourne', 'orlando-daytona-beach-melbourne', 15, 1902420, '1.516%'),
    DmaMarket('535', 'Columbus, GA (Opelika, AL)', 'columbus-opelika', 127, 234450, '0.187%'),
    DmaMarket('536', 'Youngstown', 'youngstown', 118, 263000, '0.210%'),
    DmaMarket('537', 'Peoria-Bloomington', 'peoria-bloomington', 122, 246270, '0.196%'),
    DmaMarket('538', 'Rochester, NY', 'rochester-ny', 79, 435860, '0.347%'),
    DmaMarket('539', 'Tampa-St. Petersburg (Sarasota)', 'tampa-st-petersburg-sarasota', 11, 2221240, '1.770%'),
    DmaMarket('540', 'Traverse City-Cadillac', 'traverse-city-cadillac', 116, 266960, '0.213%'),
    DmaMarket('541', 'Tri-Cities, TN-VA', 'tri-cities', 101, 331520, '0.264%'),
    DmaMarket('542', 'Dayton', 'dayton', 64, 498200, '0.397%'),
    DmaMarket('543', 'Springfield-Holyoke', 'springfield-holyoke', 115, 267210, '0.213%'),
    DmaMarket('544', 'Norfolk-Portsmouth-Newport News', 'norfolk-portsmouth-newport-news', 44, 779970, '0.622%'),
    DmaMarket('545', 'Greenville-New Bern-Washington', 'greenville-new-bern-washington', 102, 319350, '0.255%'),
    DmaMarket('546', 'Columbia, SC', 'columbia-sc', 76, 450440, '0.359%'),
    DmaMarket('547', 'Chattanooga', 'chattanooga', 86, 391370, '0.312%'),
    DmaMarket('548', 'West Palm Beach-Fort Pierce', 'west-palm-beach-fort-pierce', 39, 936790, '0.747%'),
    DmaMarket('549', 'Springfield, MO', 'springfield-mo', 74, 454280, '0.362%'),
    DmaMarket('550', 'Topeka', 'topeka', 141, 176250, '0.140%'),
    DmaMarket('551', 'Lansing', 'lansing', 117, 265830, '0.212%'),
    DmaMarket('552', 'Presque Isle', 'presque-isle', 206, 120000, '0.096%'),
    DmaMarket('553', 'Wilkes Barre-Scranton-Hazleton', 'wilkes-barre-scranton-hazleton', 59, 589190, '0.470%'),
    DmaMarket('554', 'Wheeling-Steubenville', 'wheeling-steubenville', 163, 126550, '0.101%'),
    DmaMarket('555', 'Syracuse', 'syracuse', 88, 387030, '0.308%'),
    DmaMarket('556', 'Richmond-Petersburg', 'richmond-petersburg', 56, 625380, '0.498%'),
    DmaMarket('557', 'Knoxville', 'knoxville', 60, 584100, '0.465%'),
    DmaMarket('558', 'Lima', 'lima', 190, 69630, '0.056%'),
    DmaMarket('559', 'Bluefield-Beckley-Oak Hill', 'bluefield-beckley-oak-hill', 167, 119330, '0.095%'),
    DmaMarket('560', 'Raleigh-Durham (Fayetteville)', 'raleigh-durham-fayetteville', 22, 1345840, '1.072%'),
    DmaMarket('561', 'Jacksonville', 'jacksonville', 41, 840340, '0.670%'),
    DmaMarket('563', 'Grand Rapids-Kalamazoo-Battle Creek', 'grand-rapids-kalamazoo-battle-creek', 43, 801030, '0.638%'),
    DmaMarket('564', 'Charleston-Huntington', 'charleston-huntington', 82, 422160, '0.336%'),
    DmaMarket('565', 'Elmira (Corning)', 'elmira-corning', 178, 94030, '0.075%'),
    DmaMarket('566', 'Harrisburg-Lancaster-Lebanon-York', 'harrisburg-lancaster-lebanon-york', 42, 802360, '0.639%'),
    DmaMarket('567', 'Greenville-Spartanburg-Asheville-Anderson', 'greenville-spartanburg-asheville-anderson', 36, 987740, '0.787%'),
    DmaMarket('569', 'Harrisonburg', 'harrisonburg', 173, 100920, '0.080%'),
    DmaMarket('570', 'Myrtle Beach-Florence', 'myrtle-beach-florence', 97, 347660, '0.277%'),
    DmaMarket('571', 'Ft. Myers-Naples', 'fort-myers-naples', 53, 641850, '0.511%'),
    DmaMarket('573', 'Roanoke-Lynchburg', 'roanoke-lynchburg', 70, 460000, '0.367%'),
    DmaMarket('574', 'Johnstown-Altoona-State College', 'johnstown-altoona-state-college', 112, 285520, '0.228%'),
    DmaMarket('575', 'Chattanooga', 'chattanooga', 86, 391370, '0.312%'),
    DmaMarket('576', 'Salisbury', 'salisbury', 131, 198930, '0.159%'),
    DmaMarket('577', 'Wilkes Barre-Scranton', 'wilkes-barre-scranton-hazleton', 59, 589190, '0.470%'),
    DmaMarket('578', 'Wichita-Hutchinson Plus', 'wichita-hutchinson-plus', 71, 458990, '0.366%'),
    DmaMarket('581', 'Terre Haute', 'terre-haute', 159, 142660, '0.114%'),
    DmaMarket('582', 'Lafayette, IN', 'lafayette-in', 189, 74620, '0.060%'),
    DmaMarket('583', 'Alpena', 'alpena', 208, 110000, '0.088%'),
    DmaMarket('584', 'Charlottesville', 'charlottesville', 176, 99260, '0.079%'),
    DmaMarket('588', 'South Bend-Elkhart', 'south-bend-elkhart', 100, 331800, '0.264%'),
    DmaMarket('592', 'Gainesville', 'gainesville', 157, 146560, '0.117%'),
    DmaMarket('596', 'Zanesville', 'zanesville', 203, 120000, '0.096%'),
    DmaMarket('597', 'Parkersburg', 'parkersburg', 194, 60660, '0.048%'),
    DmaMarket('598', 'Clarksburg-Weston', 'clarksburg-weston', 172, 101120, '0.081%'),
    DmaMarket('600', 'Corpus Christi', 'corpus-christi', 130, 209780, '0.167%'),
    DmaMarket('602', 'Chicago', 'chicago', 3, 3654750, '2.912%'),
    DmaMarket('604', 'Columbia-Jefferson City', 'columbia-jefferson-city', 135, 190370, '0.152%'),
    DmaMarket('605', 'Topeka', 'topeka', 141, 176250, '0.140%'),
    DmaMarket('606', 'Dothan', 'dothan', 170, 108770, '0.087%'),
    DmaMarket('609', 'St. Louis', 'saint-louis', 24, 1273870, '1.015%'),
    DmaMarket('610', 'Rockford', 'rockford', 137, 180910, '0.144%'),
    DmaMarket('611', 'Rochester-Mason City-Austin', 'rochester-mason-city-austin', 153, 152720, '0.122%'),
    DmaMarket('612', 'Shreveport', 'shreveport', 91, 375030, '0.299%'),
    DmaMarket('613', 'Minneapolis-St. Paul', 'minneapolis-saint-paul', 16, 1886680, '1.503%'),
    DmaMarket('614', 'Champaign & Springfield-Decatur', 'champaign-springfield-decatur', 92, 371520, '0.296%'),
    DmaMarket('616', 'Kansas City', 'kansas-city', 33, 1033680, '0.824%'),
    DmaMarket('617', 'Milwaukee', 'milwaukee', 38, 944900, '0.753%'),
    DmaMarket('618', 'Houston', 'houston', 6, 2797420, '2.229%'),
    DmaMarket('619', 'Lincoln & Hastings-Kearney', 'lincoln-hastings-kearney', 107, 296500, '0.236%'),
    DmaMarket('622', 'New Orleans', 'new-orleans', 50, 672790, '0.536%'),
    DmaMarket('623', 'Dallas-Fort Worth', 'dallas-fort-worth', 4, 3264490, '2.601%'),
    DmaMarket('624', 'Waco-Temple-Bryan', 'waco-temple-bryan', 83, 419600, '0.334%'),
    DmaMarket('625', 'Wichita Falls & Lawton', 'wichita-falls-lawton', 150, 156680, '0.125%'),
    DmaMarket('626', 'Victoria', 'victoria', 204, 120000, '0.096%'),
    DmaMarket('627', 'Laredo', 'laredo', 184, 84750, '0.068%'),
    DmaMarket('628', 'Monroe-El Dorado', 'monroe-el-dorado', 142, 171300, '0.137%'),
    DmaMarket('630', 'Birmingham (Anniston and Tuscaloosa)', 'birmingham-anniston-tuscaloosa', 45, 771860, '0.615%'),
    DmaMarket('631', 'Ottumwa-Kirksville', 'ottumwa-kirksville', 200, 47020, '0.038%'),
    DmaMarket('632', 'Paducah-Cape Girardeau-Harrisburg', 'paducah-cape-girardeau-harrisburg', 90, 378520, '0.302%'),
    DmaMarket('633', 'Odessa-Midland', 'odessa-midland', 144, 169390, '0.135%'),
    DmaMarket('634', 'Amarillo', 'amarillo', 132, 198790, '0.158%'),
    DmaMarket('635', 'Austin', 'austin', 34, 1029800, '0.821%'),
    DmaMarket('636', 'Harlingen-Weslaco-Brownsville-McAllen', 'harlingen-weslaco-brownsville-mcallen', 80, 428240, '0.341%'),
    DmaMarket('637', 'Cedar Rapids-Waterloo-Iowa City & Dubuque', 'cedar-rapids-waterloo-iowa-city-dubuque', 94, 364130, '0.290%'),
    DmaMarket('638', 'St. Joseph', 'saint-joseph', 201, 120000, '0.096%'),
    DmaMarket('639', 'Jackson, TN', 'jackson-tn', 174, 99740, '0.080%'),
    DmaMarket('640', 'Memphis', 'memphis', 51, 666300, '0.531%'),
    DmaMarket('641', 'San Antonio', 'san-antonio', 31, 1096400, '0.874%'),
    DmaMarket('642', 'Lafayette, LA', 'lafayette-la', 124, 245210, '0.195%'),
    DmaMarket('643', 'Lake Charles', 'lake-charles', 177, 97170, '0.077%'),
    DmaMarket('644', 'Alexandria, LA', 'alexandria', 183, 85710, '0.068%'),
    DmaMarket('647', 'Greenwood-Greenville', 'greenwood-greenville', 195, 59980, '0.048%'),
    DmaMarket('648', 'Champaign & Springfield-Decatur', 'champaign-springfield-decatur', 92, 371520, '0.296%'),
    DmaMarket('649', 'Evansville', 'evansville', 109, 290790, '0.232%'),
    DmaMarket('650', 'Oklahoma City', 'oklahoma-city', 47, 762700, '0.608%'),
    DmaMarket('651', 'Lubbock', 'lubbock', 140, 176410, '0.141%'),
    DmaMarket('652', 'Omaha', 'omaha', 73, 458080, '0.365%'),
    DmaMarket('656', 'Panama City', 'panama-city', 148, 163100, '0.130%'),
    DmaMarket('657', 'Sherman-Ada', 'sherman-ada', 160, 140220, '0.112%'),
    DmaMarket('658', 'Green Bay-Appleton', 'green-bay-appleton', 68, 478970, '0.382%'),
    DmaMarket('659', 'Nashville', 'nashville', 26, 1199400, '0.956%'),
    DmaMarket('661', 'San Angelo', 'san-angelo', 197, 57040, '0.046%'),
    DmaMarket('662', 'Abilene-Sweetwater', 'abilene-sweetwater', 166, 120020, '0.096%'),
    DmaMarket('669', 'Madison', 'madison', 77, 443220, '0.353%'),
    DmaMarket('670', 'Ft. Smith-Fayetteville-Springdale-Rogers', 'fort-smith-fayetteville-springdale-rogers', 96, 352410, '0.281%'),
    DmaMarket('671', 'Tulsa', 'tulsa', 61, 575780, '0.459%'),
    DmaMarket('673', 'Columbus-Tupelo-West Point-Houston', 'columbus-tupelo-west-point-houston', 134, 190950, '0.152%'),
    DmaMarket('675', 'Peoria-Bloomington', 'peoria-bloomington', 122, 246270, '0.196%'),
    DmaMarket('676', 'Duluth-Superior', 'duluth-superior', 138, 179710, '0.143%'),
    DmaMarket('678', 'Wichita-Hutchinson Plus', 'wichita-hutchinson-plus', 71, 458990, '0.366%'),
    DmaMarket('679', 'Des Moines-Ames', 'des-moines-ames', 67, 480550, '0.383%'),
    DmaMarket('682', 'Davenport-Rock Island-Moline', 'davenport-rock-island-moline', 104, 304840, '0.243%'),
    DmaMarket('686', 'Mobile-Pensacola (Ft. Walton Beach)', 'mobile-pensacola-fort-walton-beach', 57, 605340, '0.482%'),
    DmaMarket('687', 'Minot-Bismarck-Dickinson (Williston)', 'bismarck-minot-dickinson-williston', 147, 163860, '0.131%'),
    DmaMarket('691', 'Huntsville-Decatur (Florence)', 'huntsville-decatur-florence', 75, 452230, '0.360%'),
    DmaMarket('692', 'Beaumont-Port Arthur', 'beaumont-port-arthur', 143, 170420, '0.136%'),
    DmaMarket('693', 'Little Rock-Pine Bluff', 'little-rock-pine-bluff', 58, 590980, '0.471%'),
    DmaMarket('698', 'Montgomery-Selma', 'montgomery-selma', 121, 249100, '0.199%'),
    DmaMarket('702', 'La Crosse-Eau Claire', 'la-crosse-eau-claire', 129, 224120, '0.179%'),
    DmaMarket('705', 'Wausau-Rhinelander', 'wausau-rhinelander', 133, 194130, '0.155%'),
    DmaMarket('709', 'Tyler-Longview (Lufkin & Nacogdoches)', 'tyler-longview-lufkin-nacogdoches', 106, 297900, '0.237%'),
    DmaMarket('710', 'Hattiesburg-Laurel', 'hattiesburg-laurel', 168, 114160, '0.091%'),
    DmaMarket('711', 'Meridian', 'meridian', 192, 64660, '0.052%'),
    DmaMarket('716', 'Baton Rouge', 'baton-rouge', 95, 355760, '0.284%'),
    DmaMarket('717', 'Quincy-Hannibal-Keokuk', 'quincy-hannibal-keokuk', 175, 99650, '0.079%'),
    DmaMarket('718', 'Jackson, MS', 'jackson-ms', 99, 339170, '0.270%'),
    DmaMarket('722', 'Lincoln & Hastings-Kearney', 'lincoln-hastings-kearney', 107, 296500, '0.236%'),
    DmaMarket('724', 'Fargo-Valley City', 'fargo-valley-city', 113, 269310, '0.215%'),
    DmaMarket('725', 'Sioux Falls (Mitchell)', 'sioux-falls-mitchell', 111, 286600, '0.228%'),
    DmaMarket('734', 'Jonesboro', 'jonesboro', 182, 89400, '0.071%'),
    DmaMarket('736', 'Bowling Green', 'bowling-green', 180, 93320, '0.074%'),
    DmaMarket('737', 'Mankato', 'mankato', 199, 56190, '0.045%'),
    DmaMarket('740', 'North Platte', 'north-platte', 209, 100000, '0.080%'),
    DmaMarket('743', 'Anchorage', 'anchorage', 146, 165750, '0.132%'),
    DmaMarket('744', 'Honolulu', 'honolulu', 69, 470520, '0.375%'),
    DmaMarket('745', 'Fairbanks', 'fairbanks', 202, 110000, '0.088%'),
    DmaMarket('746', 'Biloxi-Gulfport', 'biloxi-gulfport', 158, 144960, '0.116%'),
    DmaMarket('747', 'Juneau', 'juneau', 207, 110000, '0.088%'),
    DmaMarket('749', 'Laredo', 'laredo', 184, 84750, '0.068%'),
    DmaMarket('751', 'Denver', 'denver', 17, 1806270, '1.439%'),
    DmaMarket('752', 'Colorado Springs-Pueblo', 'colorado-springs-pueblo', 87, 388730, '0.310%'),
    DmaMarket('753', 'Phoenix (Prescott)', 'phoenix-prescott', 12, 2198200, '1.752%'),
    DmaMarket('754', 'Butte-Bozeman', 'butte-bozeman', 185, 83590, '0.067%'),
    DmaMarket('755', 'Great Falls', 'great-falls', 191, 66390, '0.053%'),
    DmaMarket('756', 'Billings', 'billings', 165, 120120, '0.096%'),
    DmaMarket('757', 'Boise', 'boise', 98, 345250, '0.275%'),
    DmaMarket('758', 'Idaho Falls-Pocatello (Jackson)', 'idaho-falls-pocatello-jackson', 155, 148180, '0.118%'),
    DmaMarket('759', 'Cheyenne-Scottsbluff', 'cheyenne-scottsbluff', 193, 60950, '0.049%'),
    DmaMarket('760', 'Twin Falls', 'twin-falls', 188, 77070, '0.061%'),
    DmaMarket('762', 'Missoula', 'missoula', 161, 138300, '0.110%'),
    DmaMarket('764', 'Rapid City', 'rapid-city', 169, 110060, '0.088%'),
    DmaMarket('765', 'El Paso (Las Cruces)', 'el-paso-las-cruces', 89, 385080, '0.307%'),
    DmaMarket('766', 'Helena', 'helena', 205, 110000, '0.088%'),
    DmaMarket('767', 'Casper-Riverton', 'casper-riverton', 198, 56860, '0.045%'),
    DmaMarket('770', 'Salt Lake City', 'salt-lake-city', 28, 1163520, '0.927%'),
    DmaMarket('771', 'Yuma-El Centro', 'yuma-el-centro', 164, 124660, '0.099%'),
    DmaMarket('773', 'Grand Junction-Montrose', 'grand-junction-montrose', 187, 81090, '0.065%'),
    DmaMarket('789', 'Tucson (Sierra Vista)', 'tucson-sierra-vista', 65, 497660, '0.397%'),
    DmaMarket('790', 'Albuquerque-Santa Fe', 'albuquerque-santa-fe', 48, 708050, '0.564%'),
    DmaMarket('798', 'Glendive', 'glendive', 210, 100000, '0.080%'),
    DmaMarket('800', 'Bakersfield', 'bakersfield', 125, 244310, '0.195%'),
    DmaMarket('801', 'Eugene', 'eugene', 120, 256020, '0.204%'),
    DmaMarket('802', 'Eureka', 'eureka', 196, 59670, '0.048%'),
    DmaMarket('803', 'Los Angeles', 'los-angeles', 2, 5835790, '4.650%'),
    DmaMarket('804', 'Palm Springs', 'palm-springs', 145, 167060, '0.133%'),
    DmaMarket('807', 'San Francisco-Oakland-San Jose', 'san-francisco-oakland-san-jose', 10, 2542480, '2.026%'),
    DmaMarket('810', 'Yakima-Pasco-Richland-Kennewick', 'yakima-pasco-richland-kennewick', 114, 268030, '0.214%'),
    DmaMarket('811', 'Reno', 'reno', 103, 315350, '0.251%'),
    DmaMarket('813', 'Medford-Klamath Falls', 'medford-klamath-falls', 139, 176990, '0.141%'),
    DmaMarket('819', 'Seattle-Tacoma', 'seattle-tacoma', 13, 2098240, '1.672%'),
    DmaMarket('820', 'Portland, OR', 'portland-or', 23, 1277920, '1.018%'),
    DmaMarket('821', 'Bend, OR', 'bend', 186, 83160, '0.066%'),
    DmaMarket('825', 'San Diego', 'san-diego', 30, 1116150, '0.889%'),
    DmaMarket('828', 'Monterey-Salinas', 'monterey-salinas', 128, 230950, '0.184%'),
    DmaMarket('839', 'Las Vegas', 'las-vegas', 40, 896460, '0.714%'),
    DmaMarket('855', 'Santa Barbara-Santa Maria-San Luis Obispo', 'santa-barbara-santa-maria-san-luis-obispo', 123, 245950, '0.196%'),
    DmaMarket('862', 'Sacramento-Stockton-Modesto', 'sacramento-stockton-modesto', 20, 1497920, '1.194%'),
    DmaMarket('866', 'Fresno-Visalia', 'fresno-visalia', 55, 636260, '0.507%'),
    DmaMarket('868', 'Chico-Redding', 'chico-redding', 136, 188320, '0.150%'),
    DmaMarket('881', 'Spokane', 'spokane', 66, 496260, '0.395%'),
)

DMA_BY_CODE: dict[str, DmaMarket] = {m.code: m for m in DMA_MARKETS}


def normalize_dma_code(value: str | None) -> str | None:
    """Normalize Datalogix DMA code to 3-digit string; preserve XXXX unknown sentinel."""
    if value is None:
        return None
    text = str(value).strip().upper()
    if not text or text in {"X", "XXXX"}:
        return None if text in {"", "X"} else "XXXX"
    if text.isdigit():
        return text.zfill(3)
    return text


def lookup_dma(value: str | None) -> DmaMarket | None:
    code = normalize_dma_code(value)
    if not code or code == "XXXX":
        return None
    return DMA_BY_CODE.get(code)


def dma_market_name(value: str | None) -> str | None:
    market = lookup_dma(value)
    return market.market_name if market else None
