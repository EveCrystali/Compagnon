package fr.pilou.compagnon;

import static org.junit.Assert.assertEquals;

import org.junit.Test;

public class MiseAJourTest {
    @Test
    public void lectureDeVersionJson() throws Exception {
        MiseAJour.Publication p = MiseAJour.lire("{\"version\":\"0.9.7\",\"apkCode\":987654,\"zip\":\"PilouBureau.zip\",\"apk\":\"Pilou.apk\",\"commit\":\"abc1234\"}");
        assertEquals("0.9.7", p.version);
        assertEquals(987654L, p.code);
        assertEquals("https://github.com/EveCrystali/Compagnon/releases/download/v0.9.7/Pilou.apk", p.urlApk());
    }
}
