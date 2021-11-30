import requests
from const import REGIONS, SITES
from lxml import etree
import json
import traceback as tb


def search_bricklink(item_id):
    print(f"Search in bricklink: item_id={item_id}")
    headers = {'User-Agent': 'Paw/3.3.0 (Macintosh; OS X/11.6.1) GCDHTTPRequest'}
    search_url = f"https://www.bricklink.com/ajax/clone/search/searchproduct.ajax?q={item_id}&st=0&cond&type&cat&yf=0&yt=0&loc&reg=0&ca=0&ss&pmt&nmp=0&color=-1&min=0&max=0&minqty=0&nosuperlot=1&incomplete=0&showempty=1&rpp=25&pi=1&ci=0"
    try:
        resp = requests.get(search_url, headers=headers)
        data = resp.json()
        for tl in data['result']['typeList']:
            if tl['type'] == 'S':
                for item in tl['items']:
                    if 'idItem' in item:
                        detail_url = f"https://www.bricklink.com/v2/catalog/catalogitem.page?S={item['strItemNo']}"
                        row = {
                            'name': item['strItemName'],
                            'new_price': item['mNewMinPrice'],
                            'new_qty': item['n4NewQty'],
                            'new_sellers': item['n4NewSellerCnt'],
                            'detail_url': detail_url
                        }
                        return row
    except Exception as e:
        print(f"Search bricklink failed: {e}")
        tb.print_exc()


def search_lego(item_id, region):
    print(f"Search in lego: item_id={item_id}, region={region}")
    try:
        if region not in REGIONS:
            raise Exception('unknown region')
        headers = {'x-locale': REGIONS[region]}
        locale = REGIONS[region].lower()
        search_url = 'https://www.lego.com/api/graphql/SearchSuggestions'
        params = {
          "operationName": "SearchSuggestions",
          "variables": {
            "query": str(item_id),
            "visibility": {
              "includeRetiredProducts": True
            },
            "searchSessionId": 1
          },
          "query": "query SearchSuggestions($searchSessionId: Int, $query: String!, $suggestionLimit: Int, $productLimit: Int, $visibility: ProductVisibility) {\n  searchSuggestions(\n    searchSessionId: $searchSessionId\n    query: $query\n    suggestionLimit: $suggestionLimit\n    productLimit: $productLimit\n    visibility: $visibility\n  ) {\n    __typename\n    ... on Product {\n      ...Header_Product_ProductSuggestion\n      __typename\n    }\n    ... on SearchSuggestion {\n      text\n      __typename\n    }\n  }\n}\n\nfragment Header_Product_ProductSuggestion on Product {\n  id\n  productCode\n  name\n  slug\n  primaryImage(size: THUMBNAIL)\n  overrideUrl\n  ... on SingleVariantProduct {\n    variant {\n      ...Header_Variant_ProductSuggestion\n      __typename\n    }\n    __typename\n  }\n  ... on MultiVariantProduct {\n    variants {\n      ...Header_Variant_ProductSuggestion\n      __typename\n    }\n    __typename\n  }\n  ... on ReadOnlyProduct {\n    readOnlyVariant {\n      attributes {\n        pieceCount\n        ageRange\n        has3DModel\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n  __typename\n}\n\nfragment Header_Variant_ProductSuggestion on ProductVariant {\n  id\n  price {\n    formattedAmount\n    centAmount\n    __typename\n  }\n  __typename\n}\n"
        }
        resp = requests.post(search_url, json=params, headers=headers)
        data = resp.json()
        if 'data' not in data or 'searchSuggestions' not in data['data']:
            print(f"Search result: {data}")
            raise Exception('result error')
        results = data['data']['searchSuggestions']
        name = ''
        if len(results) > 0:
            result = results[0]
            name = result['name']
            slug = result['slug']
            detail_url = f"https://www.lego.com/{locale}/product/{slug}"
        else:
            print("Redirect search")
            search_url = 'https://www.lego.com/api/graphql/SearchQuery'
            params = {
                "operationName": "SearchQuery",
                "variables": {
                    "page": 1,
                    "isPaginated": True,
                    "perPage": 18,
                    "sort": {
                        "key":"RELEVANCE",
                        "direction":"ASC"
                    },
                    "filters": [

                    ],
                    "searchSession": 1,
                    "q": str(item_id),
                    "visibility": {
                        "includeFreeProducts": False,
                        "includeRetiredProducts": True
                    }
                },
                "query": "query SearchQuery($searchSessionId: Int, $q: String!, $page: Int, $perPage: Int, $filters: [Filter!], $sort: SortInput, $isPaginated: Boolean!, $visibility: ProductVisibility, $scoreFactorAttribute: String, $scoreFactorModifier: String, $scoreFactorMultiplier: String, $scoreFactorBoostMode: String) {\n  search(query: $q, visibility: $visibility) {\n    ... on RedirectAction {\n      __typename\n      url\n    }\n    ... on ProductSearchResults {\n      __typename\n      productResult(\n        page: $page\n        perPage: $perPage\n        filters: $filters\n        sort: $sort\n        scoring: {scoreFactorAttribute: $scoreFactorAttribute, scoreFactorModifier: $scoreFactorModifier, scoreFactorMultiplier: $scoreFactorMultiplier, scoreFactorBoostMode: $scoreFactorBoostMode}\n      ) @include(if: $isPaginated) {\n        ...Search_ProductResults\n        __typename\n      }\n      productResult(\n        page: $page\n        perPage: $perPage\n        filters: $filters\n        sort: $sort\n        scoring: {scoreFactorAttribute: $scoreFactorAttribute, scoreFactorModifier: $scoreFactorModifier, scoreFactorMultiplier: $scoreFactorMultiplier, scoreFactorBoostMode: $scoreFactorBoostMode}\n      ) @skip(if: $isPaginated) {\n        ...Search_ProductResults\n        __typename\n      }\n      resultFor\n      noResultContent {\n        title\n        overrideCopy\n        sections {\n          ...ContentSections\n          __typename\n        }\n        __typename\n      }\n    }\n    __typename\n  }\n}\n\nfragment Search_ProductResults on ProductQueryResult {\n  __typename\n  count\n  total\n  results {\n    ...Product_ProductItem\n    __typename\n  }\n  facets {\n    ...Facet_FacetSidebar\n    __typename\n  }\n  sortOptions {\n    ...Sort_SortOptions\n    __typename\n  }\n}\n\nfragment Product_ProductItem on Product {\n  __typename\n  id\n  productCode\n  name\n  slug\n  primaryImage(size: THUMBNAIL)\n  baseImgUrl: primaryImage\n  overrideUrl\n  ... on ReadOnlyProduct {\n    readOnlyVariant {\n      ...Variant_ReadOnlyProduct\n      __typename\n    }\n    __typename\n  }\n  ... on SingleVariantProduct {\n    variant {\n      ...Variant_ListingProduct\n      __typename\n    }\n    __typename\n  }\n  ... on MultiVariantProduct {\n    priceRange {\n      formattedPriceRange\n      formattedListPriceRange\n      __typename\n    }\n    variants {\n      ...Variant_ListingProduct\n      __typename\n    }\n    __typename\n  }\n}\n\nfragment Variant_ListingProduct on ProductVariant {\n  id\n  sku\n  salePercentage\n  attributes {\n    rating\n    maxOrderQuantity\n    availabilityStatus\n    availabilityText\n    vipAvailabilityStatus\n    vipAvailabilityText\n    canAddToBag\n    canAddToWishlist\n    vipCanAddToBag\n    onSale\n    isNew\n    ...ProductAttributes_Flags\n    __typename\n  }\n  ...ProductVariant_Pricing\n  __typename\n}\n\nfragment ProductVariant_Pricing on ProductVariant {\n  price {\n    formattedAmount\n    centAmount\n    currencyCode\n    formattedValue\n    __typename\n  }\n  listPrice {\n    formattedAmount\n    centAmount\n    __typename\n  }\n  attributes {\n    onSale\n    __typename\n  }\n  __typename\n}\n\nfragment ProductAttributes_Flags on ProductAttributes {\n  featuredFlags {\n    key\n    label\n    __typename\n  }\n  __typename\n}\n\nfragment Variant_ReadOnlyProduct on ReadOnlyVariant {\n  id\n  sku\n  attributes {\n    featuredFlags {\n      key\n      label\n      __typename\n    }\n    __typename\n  }\n  __typename\n}\n\nfragment Facet_FacetSidebar on Facet {\n  name\n  key\n  id\n  labels {\n    __typename\n    displayMode\n    name\n    labelKey\n    count\n    ... on FacetValue {\n      value\n      __typename\n    }\n    ... on FacetRange {\n      from\n      to\n      __typename\n    }\n  }\n  __typename\n}\n\nfragment Sort_SortOptions on SortOptions {\n  id\n  key\n  direction\n  label\n  __typename\n}\n\nfragment ContentSections on ContentSection {\n  ...BaseContentSections\n  ... on ProductSection {\n    removePadding\n    filterName\n    filterValue\n    ... on DisruptorProductSection {\n      ...DisruptorSection\n      __typename\n    }\n    ... on CountdownProductSection {\n      ...CountdownSection\n      __typename\n    }\n    products(\n      perPage: $perPage\n      page: $page\n      sort: $sort\n      filters: $filters\n      searchSession: $searchSessionId\n    ) @include(if: $isPaginated) {\n      ...ProductListings\n      __typename\n    }\n    products(\n      page: $page\n      perPage: $perPage\n      sort: $sort\n      filters: $filters\n      searchSession: $searchSessionId\n    ) @skip(if: $isPaginated) {\n      ...ProductListings\n      __typename\n    }\n    __typename\n  }\n  __typename\n}\n\nfragment CountdownSection on CountdownProductSection {\n  countdown {\n    ...Countdown\n    __typename\n  }\n  __typename\n}\n\nfragment DisruptorSection on DisruptorProductSection {\n  disruptor {\n    ...DisruptorData\n    __typename\n  }\n  __typename\n}\n\nfragment DisruptorData on Disruptor {\n  __typename\n  imageSrc {\n    ...ImageAsset\n    __typename\n  }\n  contrast\n  background\n  title\n  description\n  link\n  openInNewTab\n}\n\nfragment ImageAsset on ImageAssetDetails {\n  url\n  width\n  height\n  maxPixelDensity\n  format\n  __typename\n}\n\nfragment ProductListings on ProductQueryResult {\n  resultId\n  count\n  offset\n  total\n  optimizelyExperiment {\n    testId\n    variantId\n    __typename\n  }\n  results {\n    ...Product_ProductItem\n    __typename\n  }\n  facets {\n    ...Facet_FacetSidebar\n    __typename\n  }\n  sortOptions {\n    ...Sort_SortOptions\n    __typename\n  }\n  __typename\n}\n\nfragment SplitTestingSectionData on SplitTestingSection {\n  variantId\n  testId\n  optimizelyEntityId\n  inExperimentAudience\n  section {\n    ...ProductLayoutSection\n    ...Content\n    ...CarouselContentSection\n    ...CustomCarouselContentSection\n    __typename\n  }\n  __typename\n}\n\nfragment BaseContentSections on ContentSection {\n  ...ProductLayoutSection\n  ...Content\n  ...CarouselContentSection\n  ...CustomCarouselContentSection\n  ...SplitTestingSectionData\n  ... on TargetedSection {\n    fetchOnClient\n    section {\n      ...ProductLayoutSection\n      ...Content\n      ...CarouselContentSection\n      ...CustomCarouselContentSection\n      ...SplitTestingSectionData\n      __typename\n    }\n    __typename\n  }\n  __typename\n}\n\nfragment CarouselContentSection on ContentSection {\n  ... on ProductCarouselSection {\n    ...ProductCarousel_UniqueFields\n    productCarouselProducts: products(\n      page: 1\n      perPage: 16\n      sort: {key: FEATURED, direction: DESC}\n    ) {\n      ...Product_ProductItem\n      __typename\n    }\n    __typename\n  }\n  __typename\n}\n\nfragment CustomCarouselContentSection on ContentSection {\n  ... on CustomProductCarouselSection {\n    ...CustomProductCarousel_UniqueFields\n    productCarouselProducts: products(\n      page: 1\n      perPage: 16\n      sort: {key: FEATURED, direction: DESC}\n    ) {\n      ...CustomProductCarousel_ItemFields\n      __typename\n    }\n    __typename\n  }\n  __typename\n}\n\nfragment ProductLayoutSection on LayoutSection {\n  __typename\n  id\n  backgroundColor\n  removePadding\n  fullWidth\n  innerSection: section {\n    ...Content\n    ...CarouselContentSection\n    ...CustomCarouselContentSection\n    __typename\n  }\n}\n\nfragment Content on ContentSection {\n  __typename\n  id\n  ...UserGeneratedContentData\n  ...AccordionSectionData\n  ...BreadcrumbSection\n  ...CategoryListingSection\n  ...ListingBannerSection\n  ...CardContentSection\n  ...CardCarouselSection\n  ...CopyContent\n  ...CopySectionData\n  ...QuickLinksData\n  ...ContentBlockMixedData\n  ...HeroBannerData\n  ...MotionBannerData\n  ...MotionSidekickData\n  ...InPageNavData\n  ...GalleryData\n  ...TableData\n  ...CountdownBannerData\n  ...RecommendationSectionData\n  ...SidekickBannerData\n  ...TextBlockData\n  ...TextBlockSEOData\n  ...CrowdTwistWidgetSection\n  ...CrowdTwistToggleWidgetSection\n  ...CodedSection\n  ...GridSectionData\n  ...StickyCTAData\n  ...AudioSectionData\n  ...MotionSidekick1x1Data\n  ...ImageTransitionSliderData\n  ...ImageXrayViewerData\n  ...PollsSectionData\n  ...ArtNavigationData\n  ...MotionBanner16x9Data\n  ...QuickLinksAdvancedData\n  ...ArticleSectionData\n  ...RelatedArticleSectionData\n  ...FeatureExplorerSectionData\n  ...IdeaGeneratorSectionData\n  ...TabbedContentExplorerData\n  ...CustomProductCarousel_UniqueFields\n  ...CustomProductCarousel_ItemFields\n  ...CardContentRTWData\n}\n\nfragment AccordionSectionData on AccordionSection {\n  __typename\n  id\n  title\n  showTitle\n  accordionBlocks {\n    title\n    text\n    __typename\n  }\n}\n\nfragment BreadcrumbSection on BreadcrumbSection {\n  ...BreadcrumbDynamicSection\n  __typename\n}\n\nfragment BreadcrumbDynamicSection on BreadcrumbSection {\n  breadcrumbs {\n    label\n    url\n    analyticsTitle\n    __typename\n  }\n  __typename\n}\n\nfragment ListingBannerSection on ListingBannerSection {\n  ...ListingBanner\n  __typename\n}\n\nfragment ListingBanner on ListingBannerSection {\n  title\n  description\n  contrast\n  logoImage\n  backgroundImages {\n    small {\n      ...ImageAsset\n      __typename\n    }\n    medium {\n      ...ImageAsset\n      __typename\n    }\n    large {\n      ...ImageAsset\n      __typename\n    }\n    __typename\n  }\n  __typename\n}\n\nfragment CategoryListingSection on CategoryListingSection {\n  ...CategoryListing\n  __typename\n}\n\nfragment CategoryListing on CategoryListingSection {\n  title\n  description\n  thumbnailImage\n  children {\n    ...CategoryLeafSection\n    __typename\n  }\n  hasCustomContent\n  __typename\n}\n\nfragment CategoryLeafSection on CategoryListingChildren {\n  title\n  description\n  thumbnailImage\n  logoImage\n  url\n  ageRange\n  tag\n  thumbnailSrc {\n    ...ImageAsset\n    __typename\n  }\n  doesNotHaveAnAboutPage\n  __typename\n}\n\nfragment CardContentSection on CardContentSection {\n  ...CardContent\n  __typename\n}\n\nfragment CardContent on CardContentSection {\n  moduleTitle\n  showModuleTitle\n  backgroundColor\n  blocks {\n    title\n    isH1\n    description\n    textAlignment\n    primaryLogoSrc {\n      ...ImageAsset\n      __typename\n    }\n    secondaryLogoSrc {\n      ...ImageAsset\n      __typename\n    }\n    logoPosition\n    imageSrc {\n      ...ImageAsset\n      __typename\n    }\n    callToActionText\n    callToActionLink\n    callToActionUseAnalytics\n    altText\n    contrast\n    videoMedia {\n      ...VideoAssetFragment\n      __typename\n    }\n    __typename\n  }\n  __typename\n}\n\nfragment VideoAssetFragment on VideoMedia {\n  url\n  id\n  isLiveStream\n  subtitlesUrl\n  __typename\n}\n\nfragment CardCarouselSection on CardCarouselSection {\n  ...CardCarouselContent\n  __typename\n}\n\nfragment CardCarouselContent on CardCarouselSection {\n  moduleTitle\n  showModuleTitle\n  backgroundColor\n  blocks {\n    title\n    isH1\n    description\n    textAlignment\n    primaryLogoSrc {\n      ...ImageAsset\n      __typename\n    }\n    secondaryLogoSrc {\n      ...ImageAsset\n      __typename\n    }\n    logoPosition\n    imageSrc {\n      ...ImageAsset\n      __typename\n    }\n    callToActionText\n    callToActionLink\n    callToActionUseAnalytics\n    altText\n    contrast\n    videoMedia {\n      ...VideoAssetFragment\n      __typename\n    }\n    __typename\n  }\n  __typename\n}\n\nfragment CopyContent on CopyContentSection {\n  blocks {\n    title\n    body\n    textAlignment\n    titleColor\n    imageSrc {\n      ...ImageAsset\n      __typename\n    }\n    __typename\n  }\n  __typename\n}\n\nfragment CopySectionData on CopySection {\n  title\n  showTitle\n  body\n  __typename\n}\n\nfragment QuickLinksData on QuickLinkSection {\n  title\n  quickLinks {\n    title\n    isH1\n    link\n    openInNewTab\n    contrast\n    imageSrc {\n      ...ImageAsset\n      __typename\n    }\n    __typename\n  }\n  __typename\n}\n\nfragment ContentBlockMixedData on ContentBlockMixed {\n  moduleTitle\n  showModuleTitle\n  blocks {\n    title\n    isH1\n    description\n    backgroundColor\n    blockTheme\n    contentPosition\n    logoURL\n    secondaryLogoURL\n    logoPosition\n    callToActionText\n    callToActionLink\n    altText\n    backgroundImages {\n      largeImage {\n        small {\n          ...ImageAsset\n          __typename\n        }\n        large {\n          ...ImageAsset\n          __typename\n        }\n        __typename\n      }\n      smallImage {\n        small {\n          ...ImageAsset\n          __typename\n        }\n        large {\n          ...ImageAsset\n          __typename\n        }\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n  __typename\n}\n\nfragment UserGeneratedContentData on UserGeneratedContent {\n  ugcBlock {\n    title\n    text\n    ugcType\n    ugcKey\n    __typename\n  }\n  __typename\n}\n\nfragment HeroBannerData on HeroBanner {\n  heroblocks {\n    id\n    title\n    isH1\n    tagline\n    bannerTheme\n    contentVerticalPosition\n    contentHorizontalPosition\n    contentHeight\n    primaryLogoSrcNew {\n      ...ImageAsset\n      __typename\n    }\n    secondaryLogoSrcNew {\n      ...ImageAsset\n      __typename\n    }\n    videoMedia {\n      ...VideoAssetFragment\n      __typename\n    }\n    logoPosition\n    contentBackground\n    callToActionText\n    callToActionLink\n    brandedAppStoreAsset {\n      ...ImageAsset\n      __typename\n    }\n    callToActionUseAnalytics\n    secondaryCallToActionText\n    secondaryCallToActionLink\n    secondaryBrandedAppStoreAsset {\n      ...ImageAsset\n      __typename\n    }\n    secondaryCallToActionUseAnalytics\n    secondaryOpenInNewTab\n    backgroundImagesNew {\n      small {\n        ...ImageAsset\n        __typename\n      }\n      medium {\n        ...ImageAsset\n        __typename\n      }\n      large {\n        ...ImageAsset\n        __typename\n      }\n      __typename\n    }\n    altText\n    __typename\n  }\n  __typename\n}\n\nfragment GalleryData on Gallery {\n  galleryblocks {\n    id\n    contentHeight\n    primaryLogoSrcNew {\n      ...ImageAsset\n      __typename\n    }\n    videoMedia {\n      ...VideoAssetFragment\n      __typename\n    }\n    backgroundImagesNew {\n      small {\n        ...ImageAsset\n        __typename\n      }\n      medium {\n        ...ImageAsset\n        __typename\n      }\n      large {\n        ...ImageAsset\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n  __typename\n}\n\nfragment MotionBannerData on MotionBanner {\n  motionBannerBlocks {\n    id\n    title\n    isH1\n    tagline\n    bannerTheme\n    contentHorizontalPosition\n    primaryLogoSrc {\n      ...ImageAsset\n      __typename\n    }\n    secondaryLogoSrc {\n      ...ImageAsset\n      __typename\n    }\n    animatedMedia\n    videoMedia {\n      ...VideoAssetFragment\n      __typename\n    }\n    logoPosition\n    contentBackground\n    callToActionText\n    callToActionLink\n    callToActionUseAnalytics\n    backgroundImages {\n      small {\n        ...ImageAsset\n        __typename\n      }\n      medium {\n        ...ImageAsset\n        __typename\n      }\n      large {\n        ...ImageAsset\n        __typename\n      }\n      __typename\n    }\n    altText\n    __typename\n  }\n  __typename\n}\n\nfragment MotionSidekickData on MotionSidekick {\n  motionSidekickBlocks {\n    id\n    title\n    isH1\n    tagline\n    bannerTheme\n    contentHorizontalPosition\n    primaryLogoSrc {\n      ...ImageAsset\n      __typename\n    }\n    secondaryLogoSrc {\n      ...ImageAsset\n      __typename\n    }\n    animatedMedia\n    videoMedia {\n      ...VideoAssetFragment\n      __typename\n    }\n    logoPosition\n    contentBackground\n    callToActionText\n    callToActionLink\n    callToActionUseAnalytics\n    backgroundImages {\n      small {\n        ...ImageAsset\n        __typename\n      }\n      medium {\n        ...ImageAsset\n        __typename\n      }\n      large {\n        ...ImageAsset\n        __typename\n      }\n      __typename\n    }\n    altText\n    __typename\n  }\n  __typename\n}\n\nfragment InPageNavData on InPageNav {\n  inPageNavBlocks {\n    id\n    title\n    isH1\n    text\n    contrast\n    primaryLogoSrc\n    secondaryLogoSrc\n    animatedMedia\n    videoMedia {\n      url\n      id\n      subtitlesUrl\n      __typename\n    }\n    contentBackground\n    backgroundImages {\n      small\n      medium\n      large\n      __typename\n    }\n    callToActionText\n    callToActionLink\n    callToActionUseAnalytics\n    openInNewTab\n    secondaryCallToActionText\n    secondaryCallToActionLink\n    secondaryCallToActionUseAnalytics\n    secondaryOpenInNewTab\n    __typename\n  }\n  __typename\n}\n\nfragment TableData on TableSection {\n  rows {\n    isHeadingRow\n    cells\n    __typename\n  }\n  __typename\n}\n\nfragment RecommendationSectionData on RecommendationSection {\n  __typename\n  title\n  showTitle\n  recommendationType\n}\n\nfragment SidekickBannerData on SidekickBanner {\n  __typename\n  id\n  sidekickBlocks {\n    title\n    isH1\n    text\n    textAlignment\n    contrast\n    backgroundColor\n    logoSrc {\n      ...ImageAsset\n      __typename\n    }\n    secondaryLogoSrc {\n      ...ImageAsset\n      __typename\n    }\n    logoPosition\n    ctaTextPrimary: ctaText\n    ctaLinkPrimary: ctaLink\n    ctaUseAnalyticsPrimary: ctaUseAnalytics\n    brandedAppStoreAsset {\n      ...ImageAsset\n      __typename\n    }\n    ctaTextSecondary\n    ctaLinkSecondary\n    ctaUseAnalyticsSecondary\n    secondaryBrandedAppStoreAsset {\n      ...ImageAsset\n      __typename\n    }\n    contentHeight\n    bgImages {\n      large\n      __typename\n    }\n    videoMedia {\n      ...VideoAssetFragment\n      __typename\n    }\n    altText\n    __typename\n  }\n}\n\nfragment ProductCarousel_UniqueFields on ProductCarouselSection {\n  __typename\n  productCarouselTitle: title\n  showTitle\n  showAddToBag\n  seeAllLink\n}\n\nfragment TextBlockData on TextBlock {\n  textBlocks {\n    title\n    isH1\n    text\n    textAlignment\n    contrast\n    backgroundColor\n    callToActionLink\n    callToActionText\n    callToActionUseAnalytics\n    openInNewTab\n    secondaryCallToActionLink\n    secondaryCallToActionText\n    secondaryCallToActionUseAnalytics\n    secondaryOpenInNewTab\n    __typename\n  }\n  __typename\n}\n\nfragment TextBlockSEOData on TextBlockSEO {\n  textBlocks {\n    title\n    text\n    __typename\n  }\n  __typename\n}\n\nfragment CrowdTwistWidgetSection on CrowdTwistWidgetSection {\n  __typename\n  id\n  heading\n  activityId\n  rewardId\n  defaultOpen\n}\n\nfragment CrowdTwistToggleWidgetSection on CrowdTwistToggleWidgetSection {\n  __typename\n  defaultOpen\n  firstStepDescription\n  firstStepHeading\n  id\n  secondStepHeading\n  heading\n  radioButtons {\n    activityId\n    buttonLabel\n    rewardId\n    __typename\n  }\n}\n\nfragment CodedSection on CodedSection {\n  __typename\n  id\n  componentName\n  properties {\n    key\n    value\n    __typename\n  }\n  text {\n    key\n    value\n    __typename\n  }\n  media {\n    key\n    values {\n      id\n      contentType\n      fileSize\n      filename\n      url\n      title\n      __typename\n    }\n    __typename\n  }\n}\n\nfragment GridSectionData on GridSection {\n  items {\n    id\n    image\n    videoMedia {\n      ...VideoAssetFragment\n      __typename\n    }\n    href\n    text\n    textContrast\n    __typename\n  }\n  __typename\n}\n\nfragment AudioSectionData on AudioSection {\n  tracks {\n    trackArt {\n      ...ImageAsset\n      __typename\n    }\n    src\n    title\n    description\n    __typename\n  }\n  backgroundColor\n  textContrast\n  backgroundImage {\n    mobile {\n      ...ImageAsset\n      __typename\n    }\n    desktop {\n      ...ImageAsset\n      __typename\n    }\n    __typename\n  }\n  seriesTitle\n  seriesThumbnail {\n    ...ImageAsset\n    __typename\n  }\n  __typename\n}\n\nfragment StickyCTAData on StickyCTASection {\n  item {\n    backgroundColor\n    ctaBackgroundImage\n    ctaPosition\n    href\n    openInNewTab\n    text\n    textAlign\n    textContrast\n    effect\n    delay\n    __typename\n  }\n  __typename\n}\n\nfragment MotionSidekick1x1Data on MotionSidekick1x1 {\n  motionSidekickBlocks {\n    id\n    title\n    description\n    textContrast\n    contentHorizontalPosition\n    primaryLogoSrc {\n      ...ImageAsset\n      __typename\n    }\n    secondaryLogoSrc {\n      ...ImageAsset\n      __typename\n    }\n    inlineVideo {\n      ...VideoAssetFragment\n      __typename\n    }\n    fullVideo {\n      ...VideoAssetFragment\n      __typename\n    }\n    logoHorizontalPosition\n    backgroundColor\n    primaryCallToActionText\n    primaryCallToActionLink\n    primaryCallToActionUseAnalytics\n    secondaryCallToActionText\n    secondaryCallToActionLink\n    secondaryCallToActionUseAnalytics\n    __typename\n  }\n  __typename\n}\n\nfragment ImageTransitionSliderData on ImageTransitionSlider {\n  imageTransitionSliderBlocks {\n    id\n    title\n    description\n    backgroundColor\n    contrast\n    ctas {\n      link\n      text\n      useAnalytics\n      __typename\n    }\n    contentHorizontalPosition\n    firstImage {\n      ...ImageAsset\n      __typename\n    }\n    secondImage {\n      ...ImageAsset\n      __typename\n    }\n    __typename\n  }\n  __typename\n}\n\nfragment ImageXrayViewerData on ImageXrayViewer {\n  imageXrayViewerBlocks {\n    id\n    title\n    description\n    backgroundColor\n    contrast\n    ctas {\n      link\n      text\n      useAnalytics\n      __typename\n    }\n    contentHorizontalPosition\n    firstImage {\n      ...ImageAsset\n      __typename\n    }\n    secondImage {\n      ...ImageAsset\n      __typename\n    }\n    __typename\n  }\n  __typename\n}\n\nfragment PollsSectionData on PollsSection {\n  id\n  question\n  backgroundColor\n  answerFillColor\n  answerBorderColor\n  answers {\n    answer\n    id\n    __typename\n  }\n  textContrast\n  image {\n    ...ImageAsset\n    __typename\n  }\n  imageAlignment\n  pollResults {\n    answers {\n      answerId\n      count\n      __typename\n    }\n    totalVotes\n    __typename\n  }\n  showPollResults\n  submissionConfirmationTitle\n  submissionConfirmationContent\n  __typename\n}\n\nfragment ArtNavigationData on ArtNavigation {\n  artNavigationBlocks {\n    id\n    title\n    callToActionLink\n    backgroundImage {\n      ...ImageAsset\n      __typename\n    }\n    logoImage {\n      ...ImageAsset\n      __typename\n    }\n    textImage {\n      ...ImageAsset\n      __typename\n    }\n    __typename\n  }\n  __typename\n}\n\nfragment MotionBanner16x9Data on MotionBanner16x9 {\n  motionBannerBlocks {\n    id\n    title\n    isH1\n    tagline\n    contentHorizontalPosition\n    primaryLogoSrc {\n      ...ImageAsset\n      __typename\n    }\n    secondaryLogoSrc {\n      ...ImageAsset\n      __typename\n    }\n    animatedMedia\n    videoMedia {\n      ...VideoAssetFragment\n      __typename\n    }\n    logoPosition\n    contentBackground\n    callToActionText\n    callToActionLink\n    callToActionUseAnalytics\n    secondaryCallToActionText\n    secondaryCallToActionLink\n    secondaryCallToActionUseAnalytics\n    altText\n    __typename\n  }\n  __typename\n}\n\nfragment QuickLinksAdvancedData on QuickLinkAdvancedSection {\n  linkCount\n  backgroundColor\n  items {\n    title\n    link\n    openInNewTab\n    contrast\n    imageSrc {\n      small {\n        ...ImageAsset\n        __typename\n      }\n      medium {\n        ...ImageAsset\n        __typename\n      }\n      __typename\n    }\n    textAlignment\n    textAlignmentVertical\n    __typename\n  }\n  __typename\n}\n\nfragment ArticleSectionData on ArticleSection {\n  id\n  articleBlocks {\n    id\n    contentTitle\n    setAsH1\n    richText\n    width\n    product {\n      ...Product_ProductItem\n      __typename\n    }\n    productAlignment\n    backgroundColor\n    contentAlignment\n    callToActionText\n    callToActionType\n    callToActionLink\n    callToActionUseAnalytics\n    openInNewTab\n    image {\n      ...ImageAsset\n      __typename\n    }\n    caption\n    captionDarkMode\n    __typename\n  }\n  __typename\n}\n\nfragment RelatedArticleSectionData on RelatedArticleSection {\n  id\n  title\n  articles {\n    id\n    title\n    description\n    url\n    image {\n      ...ImageAsset\n      __typename\n    }\n    __typename\n  }\n  backgroundColor\n  __typename\n}\n\nfragment FeatureExplorerSectionData on FeatureExplorerSection {\n  id\n  title\n  layout {\n    containerType\n    removePadding\n    backgroundColor\n    __typename\n  }\n  backgroundGradientColors {\n    backgroundLightColor\n    backgroundDarkColor\n    __typename\n  }\n  accentColor\n  logo {\n    image\n    altText\n    __typename\n  }\n  features {\n    title\n    text\n    scene\n    position {\n      x\n      y\n      __typename\n    }\n    video\n    image\n    __typename\n  }\n  frames\n  __typename\n}\n\nfragment IdeaGeneratorSectionData on IdeaGeneratorSection {\n  id\n  title\n  layout {\n    containerType\n    removePadding\n    backgroundColor\n    __typename\n  }\n  previewContent {\n    title\n    text\n    callToActionText\n    __typename\n  }\n  mainContent {\n    startText\n    retryText\n    ideaLimit\n    unlockThreshold\n    endText\n    callToAction {\n      text\n      link\n      openInNewWindow\n      __typename\n    }\n    __typename\n  }\n  problems {\n    text\n    image\n    altText\n    tags\n    __typename\n  }\n  multipliers {\n    text\n    image\n    altText\n    tags\n    __typename\n  }\n  __typename\n}\n\nfragment TabbedContentExplorerData on TabbedContentExplorerSection {\n  __typename\n  id\n  tabs {\n    title\n    backgroundColor\n    accentColor\n    target {\n      callToActionLink\n      callToActionText\n      __typename\n    }\n    images {\n      alt\n      desktop {\n        ...ImageAsset\n        __typename\n      }\n      mobile {\n        ...ImageAsset\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n}\n\nfragment CustomProductCarousel_UniqueFields on CustomProductCarouselSection {\n  __typename\n  productCarouselTitle: title\n  showTitle\n  showAddToBag\n  seeAllLink\n  backgroundColor\n}\n\nfragment CustomProductCarousel_ItemFields on CustomProductCarouselItem {\n  product {\n    ...Product_ProductItem\n    __typename\n  }\n  imageOverride {\n    ...ImageAsset\n    __typename\n  }\n  imageBackgroundColor\n  contentBackgroundColor\n  ctaButtonColor\n  __typename\n}\n\nfragment Countdown on CountdownBannerChild {\n  title\n  isH1\n  text\n  textPosition\n  textAlignment\n  contrast\n  backgroundColor\n  callToActionLink\n  callToActionText\n  openInNewTab\n  countdownDate\n  __typename\n}\n\nfragment CountdownBannerData on CountdownBanner {\n  countdownBannerBlocks {\n    ...Countdown\n    __typename\n  }\n  __typename\n}\n\nfragment CardContentRTWData on CardContentRTWSection {\n  moduleTitle\n  showModuleTitle\n  backgroundColor\n  preferCarousel\n  hasShadow\n  blocks {\n    title\n    description\n    backgroundColor\n    textAlignment\n    imageSrc {\n      ...ImageAsset\n      __typename\n    }\n    altText\n    videoMedia {\n      ...VideoAssetFragment\n      __typename\n    }\n    __typename\n  }\n  __typename\n}\n"
            }
            resp = requests.post(search_url, json=params, headers=headers)
            data = resp.json()
            if not data or 'data' not in data or 'search' not in data['data']:
                raise Exception('empty result')
            detail_url = f"https://www.lego.com/{locale}/{data['data']['search']['url']}"
        print(f"Request {detail_url}")
        dtl_resp = requests.get(detail_url)
        html = etree.HTML(dtl_resp.content)
        flags = ','.join(html.xpath('//*[@id="main-content"]/div/div[1]/div/div[2]/div[1]/div[1]/span/text()'))
        avls = ','.join(html.xpath('//*[@id="main-content"]/div/div[1]/div/div[2]/div[3]/p/span/text()'))
        if name == '':
            name = ''.join(html.xpath('//*[@id="main-content"]/div/div[1]/div/div[2]/div[2]/h1/span/text()'))
        row = {
            'name': name,
            'flags': flags,
            'avls': avls,
            'detail_url': detail_url
        }
        return row
    except Exception as e:
        print(f"Search lego failed: {e}")
        tb.print_exc()


def init_task(rdb, socketio):
    for site in SITES:
        for lid in rdb.smembers(f"legoList:{site}"):
            ckey = f"legoItem:{site}:{lid}"
            row = rdb.get(ckey)
            if row:
                row = json.loads(row)
            else:
                row = {'item_id': lid, 'site': site, 'status': 0}
                rdb.set(ckey, json.dumps(row))
            if row['status'] == 0:
                print(f"Add task: {row}")
                row['status'] = 1
                rdb.set(ckey, json.dumps(row))
                rdb.lpush(f"legoTask:{site}", json.dumps(row))
                socketio.emit('onUpdate', row, broadcast=True, namespace='/ws')


if __name__ == '__main__':
    pass
#     # init_task()
#     # data = search_bricklink(10261)
#     data = search_lego(10257, 'United States')
#     print(data)
