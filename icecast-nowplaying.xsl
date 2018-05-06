<xsl:stylesheet xmlns:xsl = "http://www.w3.org/1999/XSL/Transform"
    version = "1.0">
<xsl:output method="text" encoding="UTF-8" indent="yes" />
<xsl:template match = "/icestats" >
<xsl:for-each select="source">
<xsl:if test="artist and artist !=''"><xsl:value-of select="artist" /> —
</xsl:if><xsl:value-of
    select="title" />
<!-- This next line is required to put a newline after the track name -->
<xsl:text>&#xa;</xsl:text>
</xsl:for-each>
</xsl:template>
</xsl:stylesheet>